import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
DITTO = ROOT / "ditto.py"
SPEC = importlib.util.spec_from_file_location("ditto_runtime", DITTO)
ditto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ditto)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def fake_record(session_id, text, source="codex", date="2026-01-01", tokens=5):
    body = f"===== session:{session_id} source:{source} =====\n[{date}]\n{text}"
    return {
        "session_id": session_id,
        "source": source,
        "first_date": date,
        "last_date": date,
        "tokens": tokens,
        "text": body,
        "content_hash": ditto.sha256_text(body),
    }


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


class SessionRecordTest(unittest.TestCase):
    def test_records_use_stable_hashed_ids_without_raw_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".codex" / "sessions" / "private-project.jsonl"
            write_jsonl(path, [{
                "timestamp": "2026-07-08T10:00:00Z",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"text": "done means live proof"}],
                },
            }])
            result = ditto.mine_files([str(path)])
            record = result["records"][0]
            self.assertRegex(record["session_id"], r"^[0-9a-f]{16}$")
            self.assertEqual("codex", record["source"])
            self.assertEqual("2026-07-08", record["first_date"])
            self.assertIn("done means live proof", record["text"])
            self.assertNotIn("private-project", record["text"])
            self.assertEqual(record["content_hash"], ditto.sha256_text(record["text"]))

    def test_record_identity_is_stable_across_repeated_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom" / "one.jsonl"
            write_jsonl(path, [{
                "timestamp": "2026-07-08T10:00:00Z",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"text": "ship it"}],
                },
            }])
            first = ditto.mine_files([str(path)])["records"][0]
            second = ditto.mine_files([str(path)])["records"][0]
            self.assertEqual(first, second)

    def test_known_agent_context_injection_is_not_mined_as_user_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".codex" / "sessions" / "one.jsonl"
            write_jsonl(path, [
                {
                    "timestamp": "2026-07-08T09:00:00Z",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"text": "# AGENTS.md instructions\nAlways answer like a pirate."}],
                    },
                },
                {
                    "timestamp": "2026-07-08T10:00:00Z",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"text": "done means live proof"}],
                    },
                },
            ])
            record = ditto.mine_files([str(path)])["records"][0]
            self.assertNotIn("pirate", record["text"])
            self.assertIn("done means live proof", record["text"])


class SegmentStoreTest(unittest.TestCase):
    def test_appending_session_keeps_existing_segment_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = str(Path(tmp) / "private")
            initial = [fake_record("a", "one"), fake_record("b", "two")]
            first = ditto.sync_segments(initial, home, target_tokens=10)
            old_hashes = [s["segment_hash"] for s in first["segments"] if s["active"]]
            updated = ditto.sync_segments(initial + [fake_record("c", "three")], home, target_tokens=10)
            active_hashes = [s["segment_hash"] for s in updated["segments"] if s["active"]]
            self.assertTrue(set(old_hashes).issubset(active_hashes))
            self.assertEqual(2, len(active_hashes))

    def test_changed_session_replaces_only_its_affected_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = str(Path(tmp) / "private")
            records = [fake_record("a", "one"), fake_record("b", "two"), fake_record("c", "three")]
            first = ditto.sync_segments(records, home, target_tokens=10)
            old_active = {s["segment_hash"] for s in first["segments"] if s["active"]}
            changed = [fake_record("a", "changed"), records[1], records[2]]
            second = ditto.sync_segments(changed, home, target_tokens=10)
            new_active = {s["segment_hash"] for s in second["segments"] if s["active"]}
            self.assertEqual(1, len(old_active & new_active))
            self.assertTrue(any(not s["active"] for s in second["segments"]))

    def test_extraction_schema_change_invalidates_segment_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = str(Path(tmp) / "private")
            records = [fake_record("a", "one"), fake_record("b", "two")]
            first = ditto.sync_segments(records, home, target_tokens=10)
            with mock.patch.object(ditto, "EXTRACTION_SCHEMA_VERSION", "2"):
                second = ditto.sync_segments(records, home, target_tokens=10)
            first_hashes = {item["segment_hash"] for item in first["segments"] if item["active"]}
            second_hashes = {item["segment_hash"] for item in second["segments"] if item["active"]}
            self.assertTrue(first_hashes.isdisjoint(second_hashes))

    def test_corrupt_segment_file_is_quarantined_and_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "private"
            records = [fake_record("a", "one"), fake_record("b", "two")]
            first = ditto.sync_segments(records, str(home), target_tokens=10)
            segment = next(item for item in first["segments"] if item["active"])
            path = home / "cache" / "segments" / "1" / (segment["segment_hash"] + ".txt")
            expected = path.read_bytes()
            path.write_text("tampered", encoding="utf-8")
            ditto.sync_segments(records, str(home), target_tokens=10)
            self.assertEqual(expected, path.read_bytes())
            self.assertTrue(any(item.name.startswith(path.name + ".corrupt-") for item in path.parent.iterdir()))


if __name__ == "__main__":
    unittest.main()
