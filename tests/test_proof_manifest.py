import unittest

from proof.manifest import build_manifest, build_pairs, build_system_freeze


TASK_IDS = (
    "work-primary",
    "work-held-out",
    "design-primary",
    "design-held-out",
    "write-primary",
    "write-held-out",
)
FIXTURE_HASHES = {task_id: f"{index + 1:064x}" for index, task_id in enumerate(TASK_IDS)}
INSTRUCTION_HASHES = {
    task_id: f"{index + 11:064x}" for index, task_id in enumerate(TASK_IDS)
}
BUDGETS = {
    "work": {"time_seconds": 900, "max_turns": 40},
    "design": {"time_seconds": 900, "max_turns": 40},
    "write": {"time_seconds": 600, "max_turns": 20},
}


def systems():
    return [
        build_system_freeze(
            host="codex",
            menu_label="Visible Codex Label",
            model_id="model-id-a",
            host_version="0.1",
            run_argv=["codex", "exec"],
            emulo_install_argv=["python", "install.py"],
            screenshot_sha256="a" * 64,
            tool_policy_sha256="b" * 64,
            permission_policy_sha256="c" * 64,
            quota_snapshot="provider receipt A",
            expected_cost="operator approval required",
        ),
        build_system_freeze(
            host="claude",
            menu_label="Visible Claude Label",
            model_id="model-id-b",
            host_version="0.2",
            run_argv=["claude", "-p"],
            emulo_install_argv=["python", "install.py"],
            screenshot_sha256="d" * 64,
            tool_policy_sha256="e" * 64,
            permission_policy_sha256="f" * 64,
            quota_snapshot="provider receipt B",
            expected_cost="operator approval required",
        ),
    ]


class ManifestTest(unittest.TestCase):
    def test_builds_24_pairs_and_48_unique_cells(self):
        pairs = build_pairs(
            systems(),
            fixture_hashes=FIXTURE_HASHES,
            instruction_hashes=INSTRUCTION_HASHES,
            profile_manifest_sha256="9" * 64,
            budgets=BUDGETS,
            seed="8" * 64,
        )

        self.assertEqual(24, len(pairs))
        cells = [cell for pair in pairs for cell in pair["cells"]]
        self.assertEqual(48, len({cell["cell_id"] for cell in cells}))
        self.assertEqual(48, len({cell["review_id"] for cell in cells}))
        for pair in pairs:
            self.assertEqual({"cold", "emulo"}, {cell["condition"] for cell in pair["cells"]})
            self.assertEqual({1, 2}, {cell["order"] for cell in pair["cells"]})
            self.assertTrue(all("cold" not in cell["review_id"] for cell in pair["cells"]))
            self.assertTrue(all("emulo" not in cell["review_id"] for cell in pair["cells"]))
            cold = next(cell for cell in pair["cells"] if cell["condition"] == "cold")
            emulo = next(cell for cell in pair["cells"] if cell["condition"] == "emulo")
            self.assertIsNone(cold["profile_manifest_sha256"])
            self.assertEqual("9" * 64, emulo["profile_manifest_sha256"])

    def test_seed_changes_hidden_order_but_not_pair_identity(self):
        kwargs = dict(
            systems=systems(),
            fixture_hashes=FIXTURE_HASHES,
            instruction_hashes=INSTRUCTION_HASHES,
            profile_manifest_sha256="9" * 64,
            budgets=BUDGETS,
        )
        left = build_pairs(seed="1" * 64, **kwargs)
        right = build_pairs(seed="2" * 64, **kwargs)

        self.assertEqual([item["pair_id"] for item in left], [item["pair_id"] for item in right])
        self.assertNotEqual(
            [[cell["condition"] for cell in item["cells"]] for item in left],
            [[cell["condition"] for cell in item["cells"]] for item in right],
        )

    def test_mini_preview_or_fast_label_is_ineligible(self):
        for label in ("5.4 Mini", "Preview Model", "Fast Role"):
            with self.subTest(label=label), self.assertRaisesRegex(
                ValueError, "ineligible system label"
            ):
                build_system_freeze(
                    "codex", label, "model", "1", ["codex"], ["python"],
                    "a" * 64, "b" * 64, "c" * 64, "quota", "cost"
                )

    def test_pair_build_rejects_missing_or_pilot_fixture(self):
        common = dict(
            systems=systems(),
            instruction_hashes=INSTRUCTION_HASHES,
            profile_manifest_sha256="9" * 64,
            budgets=BUDGETS,
            seed="8" * 64,
        )
        missing = dict(FIXTURE_HASHES)
        missing.pop("write-held-out")
        with self.assertRaisesRegex(ValueError, "exact six fixture IDs"):
            build_pairs(fixture_hashes=missing, **common)
        extra = dict(FIXTURE_HASHES, **{"pilot-work": "0" * 64})
        with self.assertRaisesRegex(ValueError, "pilot fixture"):
            build_pairs(fixture_hashes=extra, **common)

    def test_build_manifest_passes_strict_top_level_validation(self):
        frozen_systems = systems()
        pairs = build_pairs(
            frozen_systems,
            FIXTURE_HASHES,
            INSTRUCTION_HASHES,
            "9" * 64,
            BUDGETS,
            "8" * 64,
        )
        manifest = build_manifest(
            frozen_systems,
            pairs,
            profile_manifest_sha256="9" * 64,
            private_rubric_sha256="7" * 64,
            public_rubric_sha256="6" * 64,
            limitations=["small synthetic test"],
            created_at="2026-07-15T00:00:00Z",
        )

        self.assertEqual("Emulo Proof v1", manifest["benchmark"])
        self.assertEqual(24, len(manifest["pairs"]))


if __name__ == "__main__":
    unittest.main()
