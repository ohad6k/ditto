import copy
import unittest

from emulo_autopilot import contracts
from tests.autopilot_helpers import candidate_fixture


def decision_fixture(candidate_id):
    value = {
        "schema_version": contracts.DECISION_SCHEMA,
        "decision_id": "",
        "candidate_id": candidate_id,
        "decision": "approve",
        "reason": "founder-review",
        "policy_class": "review",
        "decided_at": "2026-07-16T10:02:00Z",
    }
    value["decision_id"] = contracts.decision_identity(value)
    return value


def generation_fixture(candidate_id):
    value = {
        "schema_version": contracts.GENERATION_SCHEMA,
        "generation_id": "",
        "parent_generation_id": None,
        "operation": "activate",
        "candidate_ids": [candidate_id],
        "domains": {"work": {"artifact": "work.md", "sha256": "b" * 64}},
        "created_at": "2026-07-16T10:03:00Z",
    }
    value["generation_id"] = contracts.generation_identity(value)
    return value


class CandidateContractTest(unittest.TestCase):
    def test_candidate_identity_is_content_bound(self):
        candidate = candidate_fixture()
        self.assertEqual(candidate, contracts.validate_candidate(candidate))

        changed = dict(candidate, statement="different")
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            contracts.validate_candidate(changed)

    def test_validation_returns_a_deep_copy(self):
        candidate = candidate_fixture()
        validated = contracts.validate_candidate(candidate)
        validated["evidence"][0]["session_id"] = "f" * 16
        self.assertNotEqual(
            candidate["evidence"][0]["session_id"],
            validated["evidence"][0]["session_id"],
        )

    def test_extra_candidate_key_is_rejected(self):
        candidate = dict(candidate_fixture(), status="pending")
        with self.assertRaisesRegex(ValueError, "candidate keys"):
            contracts.validate_candidate(candidate)

    def test_raw_quote_and_assistant_role_are_rejected(self):
        for extra in ({"quote": "private text"}, {"role": "assistant"}):
            candidate = candidate_fixture()
            candidate["evidence"] = [dict(candidate["evidence"][0], **extra)]
            with self.subTest(extra=extra):
                with self.assertRaisesRegex(ValueError, "evidence keys"):
                    contracts.validate_candidate(candidate)

    def test_unsupported_kind_and_domain_are_rejected(self):
        for field, value in (("kind", "guess"), ("domain", "money")):
            candidate = dict(candidate_fixture(), **{field: value})
            candidate["candidate_id"] = contracts.candidate_identity(candidate)
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    contracts.validate_candidate(candidate)

    def test_duplicate_receipts_are_rejected(self):
        candidate = candidate_fixture()
        candidate["evidence"] = [candidate["evidence"][0], candidate["evidence"][0]]
        candidate["candidate_id"] = contracts.candidate_identity(candidate)
        with self.assertRaisesRegex(ValueError, "duplicate receipt"):
            contracts.validate_candidate(candidate)

    def test_non_utc_timestamp_and_mismatched_stratum_are_rejected(self):
        bad_timestamp = candidate_fixture()
        bad_timestamp["created_at"] = "2026-07-16T10:01:00+03:00"
        with self.assertRaisesRegex(ValueError, "UTC"):
            contracts.validate_candidate(bad_timestamp)

        bad_stratum = candidate_fixture()
        bad_stratum["evidence"][0]["time_stratum"] = "2025-01"
        bad_stratum["candidate_id"] = contracts.candidate_identity(bad_stratum)
        with self.assertRaisesRegex(ValueError, "time_stratum"):
            contracts.validate_candidate(bad_stratum)

    def test_uppercase_hash_and_boolean_count_are_rejected(self):
        uppercase = candidate_fixture()
        uppercase["source_packet_hash"] = "A" * 64
        uppercase["candidate_id"] = contracts.candidate_identity(uppercase)
        with self.assertRaisesRegex(ValueError, "source_packet_hash"):
            contracts.validate_candidate(uppercase)

        boolean = candidate_fixture()
        boolean["contradiction_count"] = True
        boolean["candidate_id"] = contracts.candidate_identity(boolean)
        with self.assertRaisesRegex(ValueError, "contradiction_count"):
            contracts.validate_candidate(boolean)


class DecisionContractTest(unittest.TestCase):
    def test_valid_decision_is_content_bound(self):
        decision = decision_fixture(candidate_fixture()["candidate_id"])
        self.assertEqual(decision, contracts.validate_decision(decision))
        decision["reason"] = "changed"
        with self.assertRaisesRegex(ValueError, "decision_id"):
            contracts.validate_decision(decision)

    def test_decision_rejects_unknown_policy_and_reason_format(self):
        for field, value, message in (
            ("policy_class", "automatic", "policy_class"),
            ("reason", "Founder Review", "reason"),
        ):
            decision = decision_fixture(candidate_fixture()["candidate_id"])
            decision[field] = value
            decision["decision_id"] = contracts.decision_identity(decision)
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, message):
                    contracts.validate_decision(decision)


class GenerationContractTest(unittest.TestCase):
    def test_generation_rejects_traversal_artifact(self):
        generation = generation_fixture(candidate_fixture()["candidate_id"])
        generation["domains"]["work"]["artifact"] = "../work.md"
        generation["generation_id"] = contracts.generation_identity(generation)
        with self.assertRaisesRegex(ValueError, "artifact"):
            contracts.validate_generation(generation)

    def test_generation_requires_sorted_unique_candidates(self):
        candidate_id = candidate_fixture()["candidate_id"]
        generation = generation_fixture(candidate_id)
        generation["candidate_ids"] = [candidate_id, candidate_id]
        generation["generation_id"] = contracts.generation_identity(generation)
        with self.assertRaisesRegex(ValueError, "sorted and unique"):
            contracts.validate_generation(generation)

    def test_head_has_exact_keys_and_valid_generation_id(self):
        generation = generation_fixture(candidate_fixture()["candidate_id"])
        head = {
            "schema_version": contracts.HEAD_SCHEMA,
            "generation_id": generation["generation_id"],
        }
        self.assertEqual(head, contracts.validate_head(head))
        with self.assertRaisesRegex(ValueError, "head keys"):
            contracts.validate_head(dict(head, current=True))


if __name__ == "__main__":
    unittest.main()
