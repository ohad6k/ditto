import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ditto", ROOT / "ditto.py")
ditto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ditto)


class CodexControlEnvelopeTest(unittest.TestCase):
    def test_only_complete_codex_control_envelopes_are_filtered(self):
        controls = [
            "<subagent_notification>generated</subagent_notification>",
            '<codex_internal_context source="goal">generated</codex_internal_context>',
            "<skill>generated</skill>",
            "<codex_delegation>generated</codex_delegation>",
        ]
        kept = [
            "ordinary Codex message",
            "<arbitrary>human XML</arbitrary>",
            "<skill>incomplete envelope",
            "<skill>closed</skill> trailing text",
            "mentions <codex_delegation> inside a message",
        ]
        records = [
            {
                "type": "response_item",
                "timestamp": "2026-07-12T00:00:00Z",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": text}
                        for text in controls + kept
                    ],
                },
            },
            {
                "type": "user",
                "timestamp": "2026-07-12T00:00:01Z",
                "message": {
                    "role": "user",
                    "content": [{"text": controls[2]}],
                },
            },
            {
                "type": "user.message",
                "timestamp": "2026-07-12T00:00:02Z",
                "data": {"source": "user", "content": controls[3]},
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            texts = [text for _, text in ditto.user_messages(str(path))]

        self.assertEqual(kept + [controls[2], controls[3]], texts)


if __name__ == "__main__":
    unittest.main()
