import contextlib
import io
import json
import tempfile
import unittest

from emulo_autopilot import cli, contracts
from emulo_autopilot.store import AutopilotStore
from tests.autopilot_helpers import candidate_fixture


class AutopilotCliTest(unittest.TestCase):
    NOW = 1784210400
    NOW_TEXT = "2026-07-16T14:00:00Z"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = self.temp.name
        self.store = AutopilotStore(self.home)

    def _candidate(self, statement, risk_categories=None):
        candidate = candidate_fixture(
            statement=statement,
            risk_categories=risk_categories,
        )
        candidate["candidate_id"] = contracts.candidate_identity(candidate)
        self.store.put_candidate(candidate)
        return candidate

    def invoke(self, *arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        code = 0
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                cli.main(
                    ["--emulo-home", self.home] + list(arguments),
                    clock=lambda: self.NOW,
                )
        except SystemExit as exc:
            code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_status_and_queue_are_json(self):
        candidate = self._candidate("Review this local CLI rule.")
        code, stdout, stderr = self.invoke("status")
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertEqual("ready", json.loads(stdout)["health"])

        code, stdout, stderr = self.invoke("queue")
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        item = json.loads(stdout)["items"][0]
        self.assertEqual(candidate["candidate_id"], item["candidate_id"])
        self.assertEqual("pending", item["decision"])

    def test_review_activate_history_and_rollback_work_end_to_end(self):
        first_candidate = self._candidate("Keep the first CLI rule.")
        code, stdout, stderr = self.invoke(
            "review",
            first_candidate["candidate_id"],
            "approve",
            "--reason",
            "founder-review",
        )
        self.assertEqual((0, ""), (code, stderr))
        self.assertEqual(self.NOW_TEXT, json.loads(stdout)["decided_at"])

        code, stdout, stderr = self.invoke(
            "activate", first_candidate["candidate_id"]
        )
        self.assertEqual((0, ""), (code, stderr))
        first = json.loads(stdout)
        self.assertEqual("activate", first["operation"])

        second_candidate = self._candidate("Keep the second CLI rule.")
        self.invoke(
            "review",
            second_candidate["candidate_id"],
            "approve",
            "--reason",
            "founder-review",
        )
        code, stdout, stderr = self.invoke(
            "activate", second_candidate["candidate_id"]
        )
        self.assertEqual((0, ""), (code, stderr))
        second = json.loads(stdout)

        code, stdout, stderr = self.invoke("history")
        history = json.loads(stdout)
        self.assertEqual((0, ""), (code, stderr))
        self.assertEqual(second["generation_id"], history["active_generation_id"])
        self.assertEqual(2, len(history["generations"]))

        code, stdout, stderr = self.invoke(
            "rollback", first["generation_id"]
        )
        self.assertEqual((0, ""), (code, stderr))
        rollback = json.loads(stdout)
        self.assertEqual("rollback", rollback["operation"])
        self.assertEqual(second["generation_id"], rollback["parent_generation_id"])
        self.assertEqual(first["candidate_ids"], rollback["candidate_ids"])

    def test_rejected_policy_approval_is_json_error(self):
        candidate = self._candidate(
            "Use an unknown risky action.", risk_categories=["novel-risk"]
        )
        code, stdout, stderr = self.invoke(
            "review",
            candidate["candidate_id"],
            "approve",
            "--reason",
            "founder-review",
        )
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        error = json.loads(stderr)
        self.assertEqual("error", error["status"])
        self.assertIn("policy rejects", error["error"])

    def test_lock_recovery_requires_the_exact_visible_id(self):
        context = self.store.lock("activation-test")
        record = context.__enter__()
        try:
            code, stdout, stderr = self.invoke("status")
            status = json.loads(stdout)
            self.assertEqual((0, ""), (code, stderr))
            self.assertEqual(record["operation_id"], status["lock"]["operation_id"])

            code, stdout, stderr = self.invoke("recover-lock", "f" * 32)
            self.assertEqual(1, code)
            self.assertEqual("", stdout)
            self.assertIn("does not match", json.loads(stderr)["error"])

            code, stdout, stderr = self.invoke(
                "recover-lock", record["operation_id"]
            )
            self.assertEqual((0, ""), (code, stderr))
            recovered = json.loads(stdout)
            self.assertEqual(record["operation_id"], recovered["operation_id"])
            self.assertNotIn("pid", recovered)
            self.assertNotIn("hostname", recovered)
        finally:
            context.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
