import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_ditto():
    spec = importlib.util.spec_from_file_location("ditto", ROOT / "ditto.py")
    ditto = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ditto)
    return ditto


def codex_record(text):
    return {
        "type": "response_item",
        "timestamp": "2026-07-12T00:00:00Z",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        },
    }


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


class CodexControlEnvelopeTest(unittest.TestCase):
    def mine(self, texts):
        ditto = load_ditto()
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "session.jsonl"
            write_jsonl(log, [codex_record(t) for t in texts])
            return [t for _, t in ditto.user_messages(str(log))]

    def test_complete_control_envelopes_are_dropped(self):
        controls = [
            "<subagent_notification>generated</subagent_notification>",
            '<codex_internal_context source="goal">generated</codex_internal_context>',
            "<codex_delegation>generated</codex_delegation>",
            "<turn_aborted>generated</turn_aborted>",
            "<heartbeat>generated</heartbeat>",
        ]
        self.assertEqual([], self.mine(controls))

    def test_human_text_around_an_envelope_survives_without_the_envelope(self):
        mined = self.mine([
            "<subagent_notification>machine</subagent_notification> but keep my words",
            "back to back <turn_aborted>a</turn_aborted><heartbeat>b</heartbeat> kept",
        ])
        self.assertEqual(["but keep my words", "back to back  kept"], mined)

    def test_bare_skill_and_human_xml_are_kept(self):
        kept = [
            "ordinary Codex message",
            "<arbitrary>human XML</arbitrary>",
            "<skill>could be a human paste</skill>",
            "<turn_aborted>incomplete envelope",
        ]
        self.assertEqual(kept, self.mine(kept))

    def test_image_markers_are_stripped_and_paths_never_mined(self):
        mined = self.mine([
            'look at this <image name="shot.png" path="C:\\Users\\me\\shot.png">',
            "</image> and tell me what is wrong",
        ])
        self.assertEqual(["look at this", "and tell me what is wrong"], mined)
        self.assertNotIn("shot.png", " ".join(mined))


class CodexLogRootsTest(unittest.TestCase):
    def test_sources_include_archived_sessions(self):
        ditto = load_ditto()
        roots = [os.path.normpath(r) for r in ditto.SOURCES["codex"]]
        self.assertTrue(any(r.endswith("sessions") and "archived" not in r for r in roots))
        self.assertTrue(any(r.endswith("archived_sessions") for r in roots))

    def test_codex_home_overrides_the_base_directory(self):
        override = os.path.join(tempfile.gettempdir(), "codex-home-test")
        old = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = override
        try:
            ditto = load_ditto()
            for root in ditto.SOURCES["codex"]:
                self.assertTrue(os.path.normpath(root).startswith(os.path.normpath(override)))
        finally:
            if old is None:
                del os.environ["CODEX_HOME"]
            else:
                os.environ["CODEX_HOME"] = old


if __name__ == "__main__":
    unittest.main()
