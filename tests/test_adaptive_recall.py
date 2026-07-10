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


def receipt_fixtures(texts, sessions=None, domains=None):
    sessions = sessions or [f"s{index}" for index in range(len(texts))]
    domains = domains or [("work",) for _ in texts]
    return [
        {
            "schema_version": "1",
            "receipt_id": f"rcpt-{index:020x}",
            "session_id": sessions[index],
            "source": "codex" if index % 2 == 0 else "claude",
            "date": f"2026-{(index % 9) + 1:02d}-01",
            "ordinal": 0,
            "text": text,
            "tokens": max(1, len(text) // 4),
            "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "domain_hints": list(domains[index]),
        }
        for index, text in enumerate(texts)
    ]


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


class SalienceIndexTest(unittest.TestCase):
    def test_rare_correction_outranks_generic_request(self):
        receipts = receipt_fixtures([
            "can you help with this",
            "never call it done until you verified it live",
        ])

        scored = ditto.score_receipts(receipts)
        by_text = {item["text"]: item for item in scored}

        self.assertGreater(
            by_text[receipts[1]["text"]]["salience"],
            by_text[receipts[0]["text"]]["salience"],
        )
        self.assertIn("directive", by_text[receipts[1]["text"]]["signal_families"])

    def test_repeated_pattern_counts_distinct_sessions(self):
        receipts = receipt_fixtures(
            ["no em dash", "no em dash", "no em dash"],
            sessions=["a", "a", "b"],
        )

        scored = ditto.score_receipts(receipts)

        self.assertTrue(all(item["recurrence_sessions"] == 2 for item in scored))

    def test_domain_hints_are_nonexclusive(self):
        item = ditto.score_receipts(receipt_fixtures([
            "make the launch UI real, not a fake screenshot",
        ]))[0]

        self.assertIn("design", item["domain_hints"])
        self.assertIn("write", item["domain_hints"])

    def test_hebrew_and_mixed_unicode_round_trip_exactly(self):
        text = "אל תשתמש בצילום מסך מזויף — keep it real"

        item = ditto.score_receipts(receipt_fixtures([text]))[0]

        self.assertEqual(text, item["text"])


if __name__ == "__main__":
    unittest.main()
