import collections
import datetime
import os
import stat
import time

import emulo

from . import contracts


MAX_MESSAGE_CHARS = 2_000
MAX_TRANSIENT_BYTES = 65_536
MAX_RECEIPTS = 256

ScanResult = collections.namedtuple(
    "ScanResult",
    "state inbox transient_messages",
)


def physical_session_path(session_path):
    if emulo.OPENCODE_DB_SESSION_SEP in session_path:
        database, _, session_id = session_path.rpartition(
            emulo.OPENCODE_DB_SESSION_SEP
        )
        if database.endswith("opencode.db") and session_id:
            return database
    return session_path


def path_hash(session_path):
    physical = physical_session_path(session_path)
    normalized = os.path.normcase(os.path.realpath(os.path.abspath(physical)))
    if physical != session_path:
        _, _, session_id = session_path.rpartition(emulo.OPENCODE_DB_SESSION_SEP)
        normalized += emulo.OPENCODE_DB_SESSION_SEP + session_id
    return contracts.sha256_text(normalized)


def _file_state(session_path):
    physical = physical_session_path(session_path)
    absolute = os.path.abspath(physical)
    resolved = os.path.realpath(absolute)
    if os.path.normcase(absolute) != os.path.normcase(resolved):
        raise ValueError(
            "session path must be a regular file, not a link or reparse point"
        )
    info = os.lstat(absolute)
    is_reparse = bool(
        hasattr(info, "st_file_attributes")
        and info.st_file_attributes
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )
    if stat.S_ISLNK(info.st_mode) or is_reparse or not stat.S_ISREG(info.st_mode):
        raise ValueError(
            "session path must be a regular file, not a link or reparse point"
        )
    return absolute, {"size": info.st_size, "mtime_ns": info.st_mtime_ns}


def _utc_seconds(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def _observed_at(date_value, fallback_epoch):
    try:
        datetime.datetime.strptime(date_value, "%Y-%m-%d")
        return date_value + "T00:00:00Z"
    except (TypeError, ValueError):
        return time.strftime(
            "%Y-%m-%dT00:00:00Z",
            time.gmtime(fallback_epoch),
        )


def _fit_utf8(text, maximum_bytes):
    payload = text.encode("utf-8")
    if len(payload) <= maximum_bytes:
        return text, False
    payload = payload[:maximum_bytes]
    while payload:
        try:
            return payload.decode("utf-8", errors="strict"), True
        except UnicodeDecodeError:
            payload = payload[:-1]
    return "", True


class SessionScanner:
    def __init__(
        self,
        store,
        stable_seconds=120,
        clock=time.time,
        reader=emulo.user_messages,
    ):
        if (
            isinstance(stable_seconds, bool)
            or not isinstance(stable_seconds, int)
            or stable_seconds < 1
        ):
            raise ValueError("stable_seconds must be a positive integer")
        if not callable(clock) or not callable(reader):
            raise ValueError("clock and reader must be callable")
        self.store = store
        self.stable_seconds = stable_seconds
        self.clock = clock
        self.reader = reader

    def scan_path(self, session_path):
        _, identity = _file_state(session_path)
        now = int(self.clock())
        checkpoint_hash = path_hash(session_path)
        source = emulo.source_kind(session_path)
        previous = self.store.get_checkpoint(checkpoint_hash)
        if previous is None or previous["identity"] != identity:
            checkpoint = {
                "schema_version": contracts.CHECKPOINT_SCHEMA,
                "path_hash": checkpoint_hash,
                "source": source,
                "identity": identity,
                "unchanged_since": now,
                "processed_fingerprint": None,
            }
            self.store.put_checkpoint(checkpoint)
            state = "pending" if previous is None else "changed"
            return ScanResult(state, None, [])
        if now - previous["unchanged_since"] < self.stable_seconds:
            return ScanResult("pending", None, [])

        messages = self.reader(session_path)
        _, after_identity = _file_state(session_path)
        if after_identity != identity:
            checkpoint = dict(
                previous,
                identity=after_identity,
                unchanged_since=now,
                processed_fingerprint=None,
            )
            self.store.put_checkpoint(checkpoint)
            return ScanResult("changed", None, [])

        session_id = emulo.stable_session_id(session_path)
        fallback_epoch = identity["mtime_ns"] // 1_000_000_000
        remaining = MAX_TRANSIENT_BYTES
        truncated = 0
        receipts = []
        transient = []
        for ordinal, (date_value, text) in enumerate(messages):
            redacted = emulo.redact((text or "").strip())
            if not redacted:
                continue
            if len(receipts) >= MAX_RECEIPTS:
                truncated += 1
                continue
            was_truncated = False
            if len(redacted) > MAX_MESSAGE_CHARS:
                redacted = redacted[:MAX_MESSAGE_CHARS]
                was_truncated = True
            bounded, byte_truncated = _fit_utf8(redacted, remaining)
            if byte_truncated:
                was_truncated = True
            if was_truncated:
                truncated += 1
            if not bounded:
                continue
            remaining -= len(bounded.encode("utf-8"))
            observed_at = _observed_at(date_value, fallback_epoch)
            message_sha = contracts.sha256_text(bounded)
            receipt_identity = {
                "session_id": session_id,
                "ordinal": ordinal,
                "message_sha256": message_sha,
                "observed_at": observed_at,
            }
            receipt_id = "rcpt_" + contracts.sha256_text(
                contracts.canonical_json(receipt_identity)
            )[:20]
            receipts.append(
                {
                    "receipt_id": receipt_id,
                    "session_id": session_id,
                    "message_sha256": message_sha,
                    "observed_at": observed_at,
                    "time_stratum": observed_at[:7],
                }
            )
            transient.append({"receipt_id": receipt_id, "text": bounded})

        receipts.sort(key=lambda item: item["receipt_id"])
        fingerprint_identity = {
            "identity": identity,
            "receipt_ids": [item["receipt_id"] for item in receipts],
        }
        fingerprint = contracts.sha256_text(
            contracts.canonical_json(fingerprint_identity)
        )
        if previous["processed_fingerprint"] == fingerprint:
            return ScanResult("processed", None, [])

        checkpoint = dict(previous, processed_fingerprint=fingerprint)
        if not receipts:
            self.store.put_checkpoint(checkpoint)
            return ScanResult("empty", None, [])

        inbox = {
            "schema_version": contracts.INBOX_SCHEMA,
            "inbox_id": "",
            "session_id": session_id,
            "source": source,
            "session_fingerprint": fingerprint,
            "receipts": receipts,
            "message_count": len(receipts),
            "truncated_message_count": truncated,
            "created_at": _utc_seconds(previous["unchanged_since"]),
        }
        inbox["inbox_id"] = contracts.inbox_identity(inbox)
        self.store.put_inbox(inbox)
        self.store.put_checkpoint(checkpoint)
        return ScanResult("ready", inbox, transient)
