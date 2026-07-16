import copy
import datetime
import hashlib
import json
import re


CANDIDATE_SCHEMA = "emulo.autopilot-candidate/v1"
DECISION_SCHEMA = "emulo.autopilot-decision/v1"
GENERATION_SCHEMA = "emulo.autopilot-generation/v1"
HEAD_SCHEMA = "emulo.autopilot-head/v1"
INBOX_SCHEMA = "emulo.autopilot-inbox/v1"
CHECKPOINT_SCHEMA = "emulo.autopilot-checkpoint/v1"

KINDS = frozenset(
    {"directive", "correction", "preference", "workflow", "retirement"}
)
DOMAINS = frozenset({"work", "design", "write", "video"})
SOURCES = frozenset(
    {"codex", "claude", "copilot", "opencode", "antigravity", "custom"}
)
ID_PATTERNS = {
    "candidate": re.compile(r"^cand_[a-f0-9]{20}$"),
    "decision": re.compile(r"^dec_[a-f0-9]{20}$"),
    "generation": re.compile(r"^gen_[a-f0-9]{20}$"),
    "receipt": re.compile(r"^rcpt_[a-f0-9]{20}$"),
    "session": re.compile(r"^[a-f0-9]{16}$"),
    "sha256": re.compile(r"^[a-f0-9]{64}$"),
}


def canonical_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _mapping(value, label):
    if not isinstance(value, dict):
        raise ValueError(label + " must be an object")
    return value


def _exact_keys(value, expected, label):
    if set(value) != set(expected):
        raise ValueError(label + " keys are invalid")


def _string(value, label, minimum=1, maximum=2048):
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise ValueError(label + " must be a bounded string")
    return value


def _identifier(value, kind, label):
    if not isinstance(value, str) or not ID_PATTERNS[kind].fullmatch(value):
        raise ValueError(label + " is invalid")
    return value


def _timestamp(value, label):
    if not isinstance(value, str):
        raise ValueError(label + " must be UTC seconds")
    try:
        datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError(label + " must be UTC seconds") from exc
    return value


def candidate_identity(candidate):
    identity = {
        key: value
        for key, value in candidate.items()
        if key not in {"candidate_id", "created_at"}
    }
    return "cand_" + sha256_text(canonical_json(identity))[:20]


def decision_identity(decision):
    identity = {key: value for key, value in decision.items() if key != "decision_id"}
    return "dec_" + sha256_text(canonical_json(identity))[:20]


def generation_identity(generation):
    identity = {
        key: value for key, value in generation.items() if key != "generation_id"
    }
    return "gen_" + sha256_text(canonical_json(identity))[:20]


def inbox_identity(inbox):
    identity = {
        key: value
        for key, value in inbox.items()
        if key not in {"inbox_id", "created_at"}
    }
    return "inbox_" + sha256_text(canonical_json(identity))[:20]


def validate_candidate(value):
    value = _mapping(copy.deepcopy(value), "candidate")
    keys = {
        "schema_version",
        "candidate_id",
        "kind",
        "domain",
        "statement",
        "scope",
        "evidence",
        "contradiction_count",
        "risk_categories",
        "source_packet_hash",
        "prompt_contract_version",
        "created_at",
    }
    _exact_keys(value, keys, "candidate")
    if value["schema_version"] != CANDIDATE_SCHEMA:
        raise ValueError("unsupported candidate schema")
    _identifier(value["candidate_id"], "candidate", "candidate_id")
    if value["kind"] not in KINDS:
        raise ValueError("candidate kind is invalid")
    if value["domain"] not in DOMAINS:
        raise ValueError("candidate domain is invalid")
    _string(value["statement"], "candidate statement", 1, 2000)
    if any(ord(character) < 32 or ord(character) == 127
           for character in value["statement"]):
        raise ValueError("candidate statement contains a control character")
    if not isinstance(value["scope"], list) or len(value["scope"]) > 16:
        raise ValueError("candidate scope is invalid")
    if any(
        not isinstance(item, str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", item)
        for item in value["scope"]
    ):
        raise ValueError("candidate scope item is invalid")
    if value["scope"] != sorted(set(value["scope"])):
        raise ValueError("candidate scope must be sorted and unique")
    if not isinstance(value["evidence"], list) or not 1 <= len(value["evidence"]) <= 64:
        raise ValueError("candidate evidence is invalid")
    receipts = set()
    for evidence in value["evidence"]:
        evidence = _mapping(evidence, "candidate evidence")
        _exact_keys(
            evidence,
            {"receipt_id", "session_id", "observed_at", "time_stratum"},
            "candidate evidence",
        )
        _identifier(evidence["receipt_id"], "receipt", "receipt_id")
        _identifier(evidence["session_id"], "session", "session_id")
        _timestamp(evidence["observed_at"], "evidence observed_at")
        if evidence["time_stratum"] != evidence["observed_at"][:7]:
            raise ValueError("evidence time_stratum does not match observed_at")
        if evidence["receipt_id"] in receipts:
            raise ValueError("duplicate receipt_id")
        receipts.add(evidence["receipt_id"])
    if (
        isinstance(value["contradiction_count"], bool)
        or not isinstance(value["contradiction_count"], int)
        or not 0 <= value["contradiction_count"] <= 1000
    ):
        raise ValueError("contradiction_count is invalid")
    if not isinstance(value["risk_categories"], list) or len(
        value["risk_categories"]
    ) > 16:
        raise ValueError("risk_categories is invalid")
    if any(
        not isinstance(item, str) or not re.fullmatch(r"[a-z][a-z-]{0,63}", item)
        for item in value["risk_categories"]
    ):
        raise ValueError("risk category is invalid")
    if value["risk_categories"] != sorted(set(value["risk_categories"])):
        raise ValueError("risk_categories must be sorted and unique")
    _identifier(value["source_packet_hash"], "sha256", "source_packet_hash")
    if (
        value["prompt_contract_version"]
        != "emulo.autopilot-candidate-prompt/v1"
    ):
        raise ValueError("unsupported prompt contract")
    _timestamp(value["created_at"], "candidate created_at")
    if value["candidate_id"] != candidate_identity(value):
        raise ValueError("candidate_id does not match content")
    return value


def validate_decision(value):
    value = _mapping(copy.deepcopy(value), "decision")
    _exact_keys(
        value,
        {
            "schema_version",
            "decision_id",
            "candidate_id",
            "decision",
            "reason",
            "policy_class",
            "decided_at",
        },
        "decision",
    )
    if value["schema_version"] != DECISION_SCHEMA:
        raise ValueError("unsupported decision schema")
    _identifier(value["decision_id"], "decision", "decision_id")
    _identifier(value["candidate_id"], "candidate", "candidate_id")
    if value["decision"] not in {"approve", "reject"}:
        raise ValueError("decision is invalid")
    _string(value["reason"], "decision reason", 1, 200)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,199}", value["reason"]):
        raise ValueError("decision reason is invalid")
    if value["policy_class"] not in {"safe", "review", "reject"}:
        raise ValueError("policy_class is invalid")
    _timestamp(value["decided_at"], "decision decided_at")
    if value["decision_id"] != decision_identity(value):
        raise ValueError("decision_id does not match content")
    return value


def validate_generation(value):
    value = _mapping(copy.deepcopy(value), "generation")
    _exact_keys(
        value,
        {
            "schema_version",
            "generation_id",
            "parent_generation_id",
            "operation",
            "candidate_ids",
            "domains",
            "created_at",
        },
        "generation",
    )
    if value["schema_version"] != GENERATION_SCHEMA:
        raise ValueError("unsupported generation schema")
    _identifier(value["generation_id"], "generation", "generation_id")
    if value["parent_generation_id"] is not None:
        _identifier(
            value["parent_generation_id"],
            "generation",
            "parent_generation_id",
        )
    if value["operation"] not in {"activate", "rollback"}:
        raise ValueError("generation operation is invalid")
    if not isinstance(value["candidate_ids"], list) or value[
        "candidate_ids"
    ] != sorted(set(value["candidate_ids"])):
        raise ValueError("candidate_ids must be sorted and unique")
    for candidate_id in value["candidate_ids"]:
        _identifier(candidate_id, "candidate", "generation candidate_id")
    domains = _mapping(value["domains"], "generation domains")
    if not set(domains).issubset(DOMAINS):
        raise ValueError("generation domain is invalid")
    for domain, metadata in domains.items():
        metadata = _mapping(metadata, "generation domain metadata")
        _exact_keys(
            metadata,
            {"artifact", "sha256"},
            "generation domain metadata",
        )
        if metadata["artifact"] != domain + ".md":
            raise ValueError("generation artifact name is invalid")
        _identifier(metadata["sha256"], "sha256", "generation artifact hash")
    _timestamp(value["created_at"], "generation created_at")
    if value["generation_id"] != generation_identity(value):
        raise ValueError("generation_id does not match content")
    return value


def validate_head(value):
    value = _mapping(copy.deepcopy(value), "head")
    _exact_keys(value, {"schema_version", "generation_id"}, "head")
    if value["schema_version"] != HEAD_SCHEMA:
        raise ValueError("unsupported head schema")
    _identifier(value["generation_id"], "generation", "head generation_id")
    return value


def validate_checkpoint(value):
    value = _mapping(copy.deepcopy(value), "checkpoint")
    _exact_keys(
        value,
        {
            "schema_version",
            "path_hash",
            "source",
            "identity",
            "unchanged_since",
            "processed_fingerprint",
        },
        "checkpoint",
    )
    if value["schema_version"] != CHECKPOINT_SCHEMA:
        raise ValueError("unsupported checkpoint schema")
    _identifier(value["path_hash"], "sha256", "checkpoint path_hash")
    if value["source"] not in SOURCES:
        raise ValueError("checkpoint source is invalid")
    identity = _mapping(value["identity"], "checkpoint identity")
    _exact_keys(identity, {"size", "mtime_ns"}, "checkpoint identity")
    for key in ("size", "mtime_ns"):
        if (
            isinstance(identity[key], bool)
            or not isinstance(identity[key], int)
            or identity[key] < 0
        ):
            raise ValueError("checkpoint identity is invalid")
    if (
        isinstance(value["unchanged_since"], bool)
        or not isinstance(value["unchanged_since"], int)
        or value["unchanged_since"] < 0
    ):
        raise ValueError("checkpoint unchanged_since is invalid")
    if value["processed_fingerprint"] is not None:
        _identifier(
            value["processed_fingerprint"],
            "sha256",
            "processed_fingerprint",
        )
    return value


def validate_inbox(value):
    value = _mapping(copy.deepcopy(value), "inbox")
    _exact_keys(
        value,
        {
            "schema_version",
            "inbox_id",
            "session_id",
            "source",
            "session_fingerprint",
            "receipts",
            "message_count",
            "truncated_message_count",
            "created_at",
        },
        "inbox",
    )
    if value["schema_version"] != INBOX_SCHEMA:
        raise ValueError("unsupported inbox schema")
    if not isinstance(value["inbox_id"], str) or not re.fullmatch(
        r"inbox_[a-f0-9]{20}", value["inbox_id"]
    ):
        raise ValueError("inbox_id is invalid")
    _identifier(value["session_id"], "session", "inbox session_id")
    if value["source"] not in SOURCES:
        raise ValueError("inbox source is invalid")
    _identifier(
        value["session_fingerprint"],
        "sha256",
        "session_fingerprint",
    )
    if (
        not isinstance(value["receipts"], list)
        or not value["receipts"]
        or len(value["receipts"]) > 256
    ):
        raise ValueError("inbox receipts are invalid")
    receipt_ids = []
    for receipt in value["receipts"]:
        receipt = _mapping(receipt, "inbox receipt")
        _exact_keys(
            receipt,
            {
                "receipt_id",
                "session_id",
                "message_sha256",
                "observed_at",
                "time_stratum",
            },
            "inbox receipt",
        )
        _identifier(receipt["receipt_id"], "receipt", "receipt_id")
        _identifier(receipt["message_sha256"], "sha256", "message_sha256")
        if receipt["session_id"] != value["session_id"]:
            raise ValueError("receipt session_id does not match inbox")
        _timestamp(receipt["observed_at"], "receipt observed_at")
        if receipt["time_stratum"] != receipt["observed_at"][:7]:
            raise ValueError("receipt time_stratum does not match observed_at")
        receipt_ids.append(receipt["receipt_id"])
    if receipt_ids != sorted(set(receipt_ids)):
        raise ValueError("receipt IDs must be sorted and unique")
    for key in ("message_count", "truncated_message_count"):
        if (
            isinstance(value[key], bool)
            or not isinstance(value[key], int)
            or value[key] < 0
        ):
            raise ValueError(key + " is invalid")
    if value["message_count"] != len(value["receipts"]):
        raise ValueError("message_count does not match receipts")
    _timestamp(value["created_at"], "inbox created_at")
    if value["inbox_id"] != inbox_identity(value):
        raise ValueError("inbox_id does not match content")
    return value
