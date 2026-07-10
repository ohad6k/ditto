import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DITTO = ROOT / "ditto.py"
SPEC = importlib.util.spec_from_file_location("ditto_runtime", DITTO)
ditto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ditto)


class PluginRuntimeCliTest(unittest.TestCase):
    def test_plugin_status_uses_ditto_home_and_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "private"
            result = subprocess.run(
                [sys.executable, str(DITTO), "plugin", "status", "--ditto-home", str(home)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual("missing", payload["status"])
            self.assertEqual(str(home.resolve()), payload["ditto_home"])
            self.assertFalse(home.exists())

    def test_legacy_dry_run_still_uses_legacy_parser(self):
        result = subprocess.run(
            [sys.executable, str(DITTO), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("--dry-run", result.stdout)
        self.assertNotIn("plugin status", result.stdout)

    def test_private_child_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "private state"):
                ditto.safe_private_child(str(Path(tmp) / "private"), "runs", "..", "outside")


if __name__ == "__main__":
    unittest.main()
