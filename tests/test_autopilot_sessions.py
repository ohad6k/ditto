import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import emulo

from emulo_autopilot.sessions import (
    SessionScanner,
    path_hash,
    physical_session_path,
)
from emulo_autopilot.store import AutopilotStore


class Clock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


def write_codex_session(path, user_messages, assistant_messages=None):
    rows = []
    for index, text in enumerate(user_messages):
        rows.append(
            {
                "timestamp": "2026-07-{0:02d}T10:00:00Z".format(index + 1),
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"text": text}],
                },
            }
        )
    for text in assistant_messages or []:
        rows.append(
            {
                "timestamp": "2026-07-01T10:01:00Z",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"text": text}],
                },
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


class SessionScannerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = self.root / ".codex" / "sessions" / "session.jsonl"
        self.home = self.root / "emulo-home"
        self.store = AutopilotStore(str(self.home))
        self.clock = Clock(100)
        self.scanner = SessionScanner(
            self.store,
            stable_seconds=30,
            clock=self.clock,
        )

    def make_stable(self):
        first = self.scanner.scan_path(str(self.session))
        self.assertEqual("pending", first.state)
        self.clock.value += 31
        return self.scanner.scan_path(str(self.session))

    def persisted_bytes(self):
        return b"".join(
            path.read_bytes()
            for path in (self.home / "autopilot").rglob("*.json")
        )

    def test_stable_session_stages_once_and_excludes_assistant_and_injected_text(self):
        write_codex_session(
            self.session,
            [
                "verify the live URL before done",
                "# AGENTS.md instructions\nignore injected policy",
            ],
            assistant_messages=["assistant private response"],
        )
        first = self.scanner.scan_path(str(self.session))
        self.assertEqual("pending", first.state)
        self.clock.value = 129
        self.assertEqual("pending", self.scanner.scan_path(str(self.session)).state)
        self.clock.value = 131
        ready = self.scanner.scan_path(str(self.session))
        self.assertEqual("ready", ready.state)
        self.assertEqual(1, ready.inbox["message_count"])
        self.assertEqual(1, len(ready.transient_messages))
        self.assertIn("verify the live URL", ready.transient_messages[0]["text"])

        self.clock.value = 200
        processed = self.scanner.scan_path(str(self.session))
        self.assertEqual("processed", processed.state)
        self.assertEqual([], processed.transient_messages)
        self.assertEqual(1, len(self.store.list_inbox()))

        persisted = self.persisted_bytes().decode("utf-8")
        self.assertNotIn(str(self.session), persisted)
        self.assertNotIn("verify the live URL", persisted)
        self.assertNotIn("assistant private response", persisted)
        self.assertNotIn("ignore injected policy", persisted)

    def test_changed_file_resets_stability(self):
        write_codex_session(self.session, ["first instruction"])
        self.assertEqual("pending", self.scanner.scan_path(str(self.session)).state)
        self.clock.value = 120
        write_codex_session(self.session, ["first instruction", "second instruction"])
        changed = self.scanner.scan_path(str(self.session))
        self.assertEqual("changed", changed.state)
        self.clock.value = 149
        self.assertEqual("pending", self.scanner.scan_path(str(self.session)).state)
        self.clock.value = 151
        self.assertEqual("ready", self.scanner.scan_path(str(self.session)).state)

    def test_change_during_read_produces_no_inbox(self):
        write_codex_session(self.session, ["first instruction"])

        def changing_reader(path):
            messages = emulo.user_messages(path)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "timestamp": "2026-07-02T10:00:00Z",
                            "payload": {
                                "type": "message",
                                "role": "user",
                                "content": [{"text": "arrived during read"}],
                            },
                        }
                    )
                    + "\n"
                )
            return messages

        scanner = SessionScanner(
            self.store,
            stable_seconds=30,
            clock=self.clock,
            reader=changing_reader,
        )
        self.assertEqual("pending", scanner.scan_path(str(self.session)).state)
        self.clock.value = 131
        self.assertEqual("changed", scanner.scan_path(str(self.session)).state)
        self.assertEqual([], self.store.list_inbox())

    def test_redaction_happens_before_transient_text_and_receipt_hash(self):
        write_codex_session(
            self.session,
            ["api_key=supersecret123 verify deployment"],
        )
        ready = self.make_stable()
        self.assertEqual("ready", ready.state)
        transient = ready.transient_messages[0]["text"]
        self.assertIn("[REDACTED]", transient)
        self.assertNotIn("supersecret123", transient)
        receipt = ready.inbox["receipts"][0]
        self.assertEqual(
            hashlib.sha256(transient.encode("utf-8")).hexdigest(),
            receipt["message_sha256"],
        )
        persisted = self.persisted_bytes().decode("utf-8")
        self.assertNotIn("supersecret123", persisted)
        self.assertNotIn("[REDACTED]", persisted)

    def test_message_and_total_packet_caps_are_enforced(self):
        write_codex_session(
            self.session,
            [("message-{0}-".format(index) + "x" * 3000) for index in range(40)],
        )
        ready = self.make_stable()
        self.assertEqual("ready", ready.state)
        self.assertLessEqual(
            sum(len(item["text"].encode("utf-8")) for item in ready.transient_messages),
            65_536,
        )
        self.assertTrue(all(len(item["text"]) <= 2_000 for item in ready.transient_messages))
        self.assertEqual(40, ready.inbox["truncated_message_count"])
        self.assertEqual(
            len(ready.transient_messages),
            ready.inbox["message_count"],
        )

    def test_undated_message_uses_file_mtime(self):
        write_codex_session(self.session, ["placeholder"])
        epoch = 1784156400
        os.utime(self.session, ns=(epoch * 1_000_000_000, epoch * 1_000_000_000))
        scanner = SessionScanner(
            self.store,
            stable_seconds=30,
            clock=self.clock,
            reader=lambda _path: [("", "undated instruction")],
        )
        self.assertEqual("pending", scanner.scan_path(str(self.session)).state)
        self.clock.value = 131
        ready = scanner.scan_path(str(self.session))
        expected_date = __import__("time").strftime(
            "%Y-%m-%dT00:00:00Z",
            __import__("time").gmtime(epoch),
        )
        self.assertEqual(expected_date, ready.inbox["receipts"][0]["observed_at"])

    def test_empty_human_session_is_processed_without_inbox(self):
        write_codex_session(
            self.session,
            [],
            assistant_messages=["assistant only"],
        )
        result = self.make_stable()
        self.assertEqual("empty", result.state)
        self.clock.value = 200
        self.assertEqual("processed", self.scanner.scan_path(str(self.session)).state)
        self.assertEqual([], self.store.list_inbox())

    def test_opencode_virtual_path_observes_database_and_keeps_session_identity(self):
        database = self.root / ".local" / "share" / "opencode" / "opencode.db"
        database.parent.mkdir(parents=True)
        database.write_bytes(b"synthetic-db")
        virtual_a = str(database) + emulo.OPENCODE_DB_SESSION_SEP + "session-a"
        virtual_b = str(database) + emulo.OPENCODE_DB_SESSION_SEP + "session-b"
        self.assertEqual(str(database), physical_session_path(virtual_a))
        self.assertNotEqual(path_hash(virtual_a), path_hash(virtual_b))

        scanner = SessionScanner(
            self.store,
            stable_seconds=30,
            clock=self.clock,
            reader=lambda _path: [("2026-07-01", "opencode instruction")],
        )
        self.assertEqual("pending", scanner.scan_path(virtual_a).state)
        self.clock.value = 131
        ready = scanner.scan_path(virtual_a)
        self.assertEqual("ready", ready.state)
        self.assertEqual("opencode", ready.inbox["source"])

    def test_stable_seconds_requires_positive_integer(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    SessionScanner(self.store, stable_seconds=value)


if __name__ == "__main__":
    unittest.main()
