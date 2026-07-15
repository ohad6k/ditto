import json
import tempfile
import unittest
from pathlib import Path

from proof.fixtures import reset_fixture, tree_hash
from proof.pilot import build_pilot_package, build_pilot_plan, load_pilot_registry


ROOT = Path(__file__).resolve().parents[1]
PILOT_ROOT = ROOT / "proof" / "fixtures" / "pilot"


class PilotFixtureTest(unittest.TestCase):
    def test_pilot_has_three_non_scored_families(self):
        registry = load_pilot_registry(PILOT_ROOT / "registry.json")
        self.assertEqual(
            {"work", "design", "write"},
            {item["family"] for item in registry["tasks"]},
        )
        self.assertTrue(all(item["scored"] is False for item in registry["tasks"]))
        self.assertTrue(
            all(item["task_id"].startswith("pilot-") for item in registry["tasks"])
        )

    def test_fixture_contracts_are_machine_readable_and_fictional(self):
        registry = load_pilot_registry(PILOT_ROOT / "registry.json")
        for task in registry["tasks"]:
            fixture = PILOT_ROOT / task["path"]
            self.assertEqual(task["fixture_sha256"], tree_hash(fixture))
            contract = json.loads(
                (fixture / task["contract"]).read_text(encoding="utf-8")
            )
            self.assertEqual(task["family"], contract["family"])
            self.assertTrue(contract["required_outputs"])
            text = json.dumps(contract).casefold()
            self.assertNotIn("ohad", text)
            self.assertNotIn("ditto", text)

    def test_six_cells_are_isolated_opaque_and_non_scored(self):
        registry = load_pilot_registry(PILOT_ROOT / "registry.json")
        cells = build_pilot_plan(registry, seed="pilot-seed")
        self.assertEqual(6, len(cells))
        self.assertEqual(6, len({item["cell_id"] for item in cells}))
        self.assertEqual(6, len({item["review_id"] for item in cells}))
        self.assertEqual({"cold", "ditto"}, {item["condition"] for item in cells})
        self.assertTrue(all(item["scored"] is False for item in cells))
        self.assertTrue(
            all(
                "cold" not in item["review_id"]
                and "ditto" not in item["review_id"]
                for item in cells
            )
        )

    def test_resets_are_deterministic_and_cell_roots_differ(self):
        registry = load_pilot_registry(PILOT_ROOT / "registry.json")
        work = next(item for item in registry["tasks"] if item["family"] == "work")
        source = PILOT_ROOT / work["path"]
        with tempfile.TemporaryDirectory() as root:
            first = reset_fixture(source, Path(root) / "cold", work["fixture_sha256"])
            second = reset_fixture(source, Path(root) / "ditto", work["fixture_sha256"])
            self.assertNotEqual(first, second)
            self.assertEqual(tree_hash(first), tree_hash(second))

    def test_simulated_capture_is_sanitized_and_non_comparable(self):
        registry = load_pilot_registry(PILOT_ROOT / "registry.json")
        cells = build_pilot_plan(registry, seed="pilot-seed")
        records = []
        for index, cell in enumerate(cells):
            records.append(
                {
                    **cell,
                    "objective_checks": {"contract_captured": True},
                    "blind_review": {"captured": True, "verdict": "tie"},
                    "artifact_sha256": f"{index + 1:064x}",
                    "redaction_state": "passed",
                    "public_note": "synthetic pilot record",
                }
            )
        package = build_pilot_package(records, canaries={"private": "CANARY-PRIVATE"})
        self.assertEqual("pilot", package["label"])
        self.assertFalse(package["scored"])
        self.assertFalse(package["comparable"])
        self.assertEqual(6, package["execution_count"])
        self.assertTrue(
            all(item["objective_checks"] for item in package["records"])
        )
        self.assertTrue(all(item["blind_review"] for item in package["records"]))

        records[0]["public_note"] = "CANARY-PRIVATE"
        with self.assertRaisesRegex(ValueError, "privacy scan failed"):
            build_pilot_package(records, canaries={"private": "CANARY-PRIVATE"})


if __name__ == "__main__":
    unittest.main()
