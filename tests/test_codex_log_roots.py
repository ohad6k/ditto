import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DITTO = ROOT / "ditto.py"


def write_session(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "timestamp": "2026-07-12T00:00:00Z",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [{"text": text}],
        },
    }) + "\n", encoding="utf-8")


class CodexLogRootsTest(unittest.TestCase):
    def test_preflight_reads_active_and_archived_codex_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / ".codex"
            private_home = root / "ditto-home"
            write_session(codex_home / "sessions" / "active.jsonl", "active")
            write_session(
                codex_home / "archived_sessions" / "archived.jsonl",
                "archived",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(DITTO),
                    "plugin",
                    "preflight",
                    "--source",
                    "codex",
                    "--ditto-home",
                    str(private_home),
                ],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "CODEX_HOME": str(codex_home)},
            )

            self.assertEqual(2, json.loads(result.stdout)["valid_sessions"])
            self.assertFalse(private_home.exists())


if __name__ == "__main__":
    unittest.main()
