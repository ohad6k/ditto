import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DITTO = ROOT / "ditto.py"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


class DittoCliTest(unittest.TestCase):
    def test_dry_run_counts_without_writing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs = root / "logs"
            out = root / "ditto-out"
            write_jsonl(logs / "codex.jsonl", [
                {
                    "timestamp": "2026-07-08T10:00:00Z",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"text": "done means live proof. token=abc123456789"}],
                    },
                },
                {
                    "timestamp": "2026-07-08T10:01:00Z",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"text": "ignore assistant text"}],
                    },
                },
            ])
            write_jsonl(logs / "claude.jsonl", [
                {
                    "timestamp": "2026-07-08T11:00:00Z",
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": "do not touch files outside the task",
                    },
                },
            ])

            result = subprocess.run(
                [sys.executable, str(DITTO), "--path", str(logs), "--out", str(out), "--dry-run"],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("dry run: no files written", result.stdout)
            self.assertIn("jsonl files: 2", result.stdout)
            self.assertIn("sessions: 2", result.stdout)
            self.assertIn("your messages: 2", result.stdout)
            self.assertIn("secrets/PII redacted: 1", result.stdout)
            self.assertFalse(out.exists())

    def test_run_writes_redacted_corpus_and_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs = root / "logs"
            out = root / "ditto-out"
            write_jsonl(logs / "codex.jsonl", [
                {
                    "timestamp": "2026-07-08T10:00:00Z",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"text": "api_key=supersecret123 do the smallest fix"}],
                    },
                },
                {
                    "timestamp": "2026-07-08T10:01:00Z",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"text": "assistant output should not appear"}],
                    },
                },
            ])

            result = subprocess.run(
                [sys.executable, str(DITTO), "--path", str(logs), "--out", str(out), "--chunks", "1"],
                check=True,
                capture_output=True,
                text=True,
            )

            corpus = (out / "you-corpus.txt").read_text(encoding="utf-8")
            chunk = (out / "chunks" / "chunk-01.txt").read_text(encoding="utf-8")

            self.assertIn("sessions: 1", result.stdout)
            self.assertIn("api_key=[REDACTED]", corpus)
            self.assertNotIn("supersecret123", corpus)
            self.assertNotIn("assistant output should not appear", corpus)
            self.assertEqual(corpus, chunk)


if __name__ == "__main__":
    unittest.main()
