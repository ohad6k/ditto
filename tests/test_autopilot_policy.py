import unittest

from emulo_autopilot import contracts
from emulo_autopilot.policy import classify_candidate
from tests.autopilot_helpers import candidate_fixture


class PolicyTest(unittest.TestCase):
    def test_policy_matrix(self):
        cases = [
            (
                candidate_fixture(evidence=3, strata=2),
                False,
                "review",
                "auto-disabled",
            ),
            (
                candidate_fixture(evidence=3, strata=2),
                True,
                "safe",
                "repeated-explicit-low-risk",
            ),
            (
                candidate_fixture(evidence=2, strata=2),
                True,
                "review",
                "insufficient-sessions",
            ),
            (
                candidate_fixture(evidence=3, strata=1),
                True,
                "review",
                "insufficient-time-strata",
            ),
            (
                candidate_fixture(contradiction_count=1),
                True,
                "review",
                "contradiction",
            ),
            (
                candidate_fixture(risk_categories=["external-communication"]),
                True,
                "review",
                "prohibited-risk",
            ),
            (
                candidate_fixture(kind="retirement"),
                True,
                "review",
                "retirement",
            ),
        ]
        for candidate, enabled, expected_class, expected_reason in cases:
            with self.subTest(expected_reason=expected_reason):
                result = classify_candidate(
                    candidate,
                    auto_activate_enabled=enabled,
                )
                self.assertEqual(expected_class, result.policy_class)
                self.assertEqual(expected_reason, result.reason)

    def test_duplicate_session_ids_do_not_satisfy_repetition(self):
        candidate = candidate_fixture(evidence=3, strata=2)
        for evidence in candidate["evidence"]:
            evidence["session_id"] = "1" * 16
        candidate["candidate_id"] = contracts.candidate_identity(candidate)
        result = classify_candidate(candidate, auto_activate_enabled=True)
        self.assertEqual("review", result.policy_class)
        self.assertEqual("insufficient-sessions", result.reason)

    def test_unknown_risk_category_fails_closed(self):
        candidate = candidate_fixture(risk_categories=["novel-risk"])
        result = classify_candidate(candidate, auto_activate_enabled=True)
        self.assertEqual("reject", result.policy_class)
        self.assertEqual("unknown-risk-category", result.reason)

    def test_malformed_candidate_is_rejected_before_policy(self):
        candidate = candidate_fixture()
        candidate["evidence"][0]["role"] = "assistant"
        with self.assertRaisesRegex(ValueError, "evidence keys"):
            classify_candidate(candidate, auto_activate_enabled=True)

    def test_auto_activate_flag_requires_a_real_boolean(self):
        candidate = candidate_fixture()
        for value in (1, "yes", None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "boolean"):
                    classify_candidate(candidate, auto_activate_enabled=value)


if __name__ == "__main__":
    unittest.main()
