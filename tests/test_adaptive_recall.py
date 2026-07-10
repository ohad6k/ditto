import hashlib
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ditto_adaptive", ROOT / "ditto.py")
ditto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ditto)


def make_record(session_id, messages, source="codex"):
    rendered = [f"===== session:{session_id} source:{source} ====="]
    rendered.extend(f"[{date}]\n{text}" for date, text in messages)
    text = "\n".join(rendered)
    return {
        "session_id": session_id,
        "source": source,
        "first_date": min(date for date, _ in messages),
        "last_date": max(date for date, _ in messages),
        "tokens": max(1, sum(len(value) for _, value in messages) // 4),
        "text": text,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "messages": [
            {"date": date, "text": value, "ordinal": ordinal}
            for ordinal, (date, value) in enumerate(messages)
        ],
    }


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class ReceiptLedgerTest(unittest.TestCase):
    def test_large_session_becomes_individual_stable_receipts(self):
        record = make_record("s1", [
            ("2026-01-01", "first preference"),
            ("2026-01-02", "second preference"),
        ])

        first = ditto.build_receipt_ledger([record])
        second = ditto.build_receipt_ledger([record])

        self.assertEqual(first, second)
        self.assertEqual(2, len(first))
        self.assertEqual({"s1"}, {item["session_id"] for item in first})
        self.assertTrue(all(
            re.fullmatch(r"rcpt-[a-f0-9]{20}", item["receipt_id"])
            for item in first
        ))

    def test_receipt_text_is_redacted_before_ledger_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(path, [{
                "timestamp": "2026-01-01T00:00:00Z",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"text": "use sk-" + "a" * 24}],
                },
            }])

            result = ditto.mine_files([str(path)])
            ledger = ditto.build_receipt_ledger(result["records"])

            self.assertNotIn("sk-", ledger[0]["text"])


if __name__ == "__main__":
    unittest.main()
