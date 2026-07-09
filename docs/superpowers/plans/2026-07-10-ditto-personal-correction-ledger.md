# Ditto Personal Correction Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Ditto from a one-run profile generator into an evidence-backed weekly loop that finds repeated explicit corrections, lets the user approve one behavioral patch, installs it as a separate agent skill, and checks new sessions for recurrence.

**Architecture:** Keep Ditto's default user-only profile extraction unchanged. Add a Claude Code-only, explicit opt-in correction path that extracts redacted user and assistant conversation text while excluding tool results and tool calls. An agent proposes correction candidates in a strict JSON contract; `ditto.py` validates every receipt against the extracted events, requires evidence from at least two sessions, and asks the user to approve, edit, or reject each rule before rendering a separate `ditto-corrections` skill. A later rerun extracts only new events and records user-confirmed recurrence without treating silence as success.

**Tech Stack:** Python 3 standard library, `argparse`, JSON/JSONL, Markdown agent prompts, `unittest`, Claude Code skills.

---

## Product decisions locked for this experiment

- Public story: **Ditto is the living mirror for how you work.**
- Recurring job: **Never correct the same agent twice.**
- The existing `you.md` flow remains user-authored-text only and keeps all current CLI behavior.
- Correction mining is opt-in and Claude Code-only for the 14-day gate.
- Correction traces may contain user and assistant conversational text. They exclude tool calls, tool results, and thinking blocks, but assistant prose can still contain generated code or private project details.
- A candidate is invalid unless it contains `request -> assistant behavior -> explicit user correction` receipts from at least two separate sessions.
- Silence, continued conversation, and a later successful result are not acceptance signals.
- Every generated rule requires explicit user approval or editing before installation.
- The approved patch is a separate `ditto-corrections` skill. It does not silently rewrite `you.md`.
- The first gate is Ohad dogfooding. Two external opt-in pilots may run only after the local gate passes and Ohad approves outreach.
- Persistent hooks, background watchers, automatic self-editing, profile `--diff`, workflow mining, elicitation, and additional trace sources are outside this plan.

## File map

- Modify `ditto.py`
  - Remove the card's remote image fallback.
  - Extract stable, redacted Claude conversation events for the opt-in correction flow.
  - Validate candidate receipts against real events.
  - Run the approve/edit/reject review.
  - Write `ledger.json` and a separate installable `SKILL.md`.
  - Support named skill installs without breaking the existing `you` install.
  - Extract only events newer than the ledger for a weekly review.
  - Apply user-confirmed recurrence reviews.
- Create `tests/test_corrections.py`
  - Cover trace boundaries, stable IDs, redaction, receipt validation, approval, editing, named installs, delta extraction, and recurrence review.
- Create `CORRECTION_PROMPT.md`
  - Define the candidate-mining contract and forbid unsupported inference.
- Create `CORRECTION_REVIEW_PROMPT.md`
  - Define the weekly recurrence contract and forbid interpreting silence as success.
- Create `schemas/ditto-correction-ledger-v1.schema.json`
  - Publish the stable machine-readable artifact other tools can consume.
- Create `docs/experiments/correction-benchmark.md`
  - Define the blinded baseline-versus-patch test and pass/fail gate.
- Modify `SECURITY.md`
  - Document every current and new read/write path, the opt-in assistant-text boundary, install destinations, and best-effort redaction.
- Modify `README.md`
  - Describe the correction loop as experimental, show exact commands, and state its limits.
- Modify `ROADMAP.md`
  - Put the correction ledger before broader expansion and keep later features gated.
- Modify `skills/ditto/SKILL.md`
  - Teach the agent to orchestrate extraction, candidate mining, human review, installation, and the weekly rerun.

## Four-hour daily budget

- Days 1-2: Move 1, data/security contract.
- Days 3-4: Move 2, opt-in trace extractor.
- Days 5-6: Move 3, receipt-backed candidate contract.
- Days 7-9: Move 4, approval ledger and separate skill.
- Days 10-11: Move 5, weekly delta and recurrence review.
- Days 12-14: Move 6, benchmark, dogfood proof, docs, and release decision.

---

### Move 1, Days 1-2: Make the current privacy contract true

**Files:**
- Modify: `ditto.py:282-425`
- Modify: `tests/test_ditto.py:288-325`
- Modify: `SECURITY.md`

- [ ] **Step 1: Add a failing test proving generated cards contain no remote asset URL**

Add this assertion after `html` is read in `test_card_renders_terminal_and_html`:

```python
self.assertNotIn("raw.githubusercontent.com", html)
self.assertNotIn("https://", html)
```

- [ ] **Step 2: Run the focused test and verify the current remote fallback fails it**

Run:

```powershell
python -m unittest tests.test_ditto.DittoCliTest.test_card_renders_terminal_and_html -v
```

Expected: `FAIL` because `card.html` contains `https://raw.githubusercontent.com/ohad6k/ditto/main/assets/ditto.png`.

- [ ] **Step 3: Replace the remote card fallback with a local-or-empty image slot**

Change the art block in `CARD_HTML` to:

```html
<div class="{art_class}" id="art">
  {art_image}
  <div class="nameplate"><b>{archetype}</b><div>{range}</div></div>
</div>
```

Replace the remote/local setup in `render_card_html` with:

```python
art_local = ""
local_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ditto.png")
if os.path.exists(local_png):
    try:
        out_dir = card.get("_out_dir", "")
        if out_dir:
            art_local = os.path.relpath(local_png, out_dir).replace("\\", "/")
    except ValueError:
        art_local = ""

art_class = "art" if art_local else "art noart"
art_image = ""
if art_local:
    art_image = (
        f'<img src="{esc(art_local)}" '
        'onerror="document.getElementById(\'art\').className=\'art noart\';this.remove()">'
    )
```

Pass `art_class=art_class` and `art_image=art_image` into `CARD_HTML.format`, and remove the `art_local` and `art_remote` arguments.

- [ ] **Step 4: Run the card test and the complete baseline suite**

Run:

```powershell
python -m unittest tests.test_ditto.DittoCliTest.test_card_renders_terminal_and_html -v
python -m unittest discover -s tests -v
```

Expected: the focused test passes and all 9 existing tests pass.

- [ ] **Step 5: Replace the inaccurate security read/write sections with the exact current contract**

Document these reads:

```markdown
- `~/.codex/sessions/**/*.jsonl`
- `~/.claude/projects/**/*.jsonl`
- `~/.copilot/session-state/**/*.jsonl`
- a user-supplied JSONL folder passed with `--path`
- an existing profile passed to `--install`
- `ditto-out/card.json` and `ditto-out/stats.json` when rendering a card
```

Document these writes:

```markdown
The normal mining flow writes `you-corpus.txt`, `stats.json`, and chunk files under `--out`.
The card flow writes `card.html` under `--out`.
The installer intentionally writes outside `--out` to the target selected by the user:
`~/.claude/skills`, `~/.codex/skills`, `.cursor/rules`, `AGENTS.md`, or `GEMINI.md`.
The generated card uses a repository-local image when available and makes no remote image request.
```

Keep the existing best-effort redaction warning. Replace “nothing leaves your machine” with the precise statement that `ditto.py` makes no network calls, while the later mining step is governed by the selected agent/provider.

- [ ] **Step 6: Commit the corrected contract**

```powershell
git add ditto.py tests/test_ditto.py SECURITY.md
git commit -m "fix: make ditto privacy contract match behavior"
```

**Done means:** current reads and writes are documented, the generated card has no remote fallback, and all existing tests pass.

---

### Move 2, Days 3-4: Add explicit opt-in Claude correction traces

**Files:**
- Modify: `ditto.py:23-174`
- Modify: `ditto.py:544-603`
- Create: `tests/test_corrections.py`

- [ ] **Step 1: Create test helpers and a failing extraction test**

Create `tests/test_corrections.py` with these helpers and first test:

```python
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


def claude_rows(day):
    return [
        {
            "timestamp": f"2026-07-{day:02d}T10:00:00Z",
            "type": "user",
            "message": {"role": "user", "content": "ship the fix token=abc123456789"},
        },
        {
            "timestamp": f"2026-07-{day:02d}T10:01:00Z",
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "private reasoning"},
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "secret.py"}},
                    {"type": "text", "text": "I edited the file and it should work."},
                ],
            },
        },
        {
            "timestamp": f"2026-07-{day:02d}T10:02:00Z",
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"type": "tool_result", "content": "raw tool output"},
                    {"type": "text", "text": "not done. open production and prove it"},
                ],
            },
        },
    ]


class CorrectionTraceTest(unittest.TestCase):
    def test_opt_in_trace_keeps_redacted_conversation_text_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs = root / "logs"
            out = root / "ditto-out"
            write_jsonl(logs / "project-name" / "session.jsonl", claude_rows(1))

            result = subprocess.run(
                [sys.executable, str(DITTO), "--corrections", "--path", str(logs), "--out", str(out)],
                check=True,
                capture_output=True,
                text=True,
            )

            events_path = out / "corrections" / "events.jsonl"
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            joined = json.dumps(events)

            self.assertEqual([event["role"] for event in events], ["user", "assistant", "user"])
            self.assertIn("token=[REDACTED]", joined)
            self.assertNotIn("abc123456789", joined)
            self.assertNotIn("private reasoning", joined)
            self.assertNotIn("secret.py", joined)
            self.assertNotIn("raw tool output", joined)
            self.assertNotIn("project-name", joined)
            self.assertIn("assistant messages included: 1", result.stdout)
```

- [ ] **Step 2: Add a failing dry-run boundary test**

Add:

```python
def test_correction_dry_run_writes_nothing(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        logs = root / "logs"
        out = root / "ditto-out"
        write_jsonl(logs / "session.jsonl", claude_rows(1))

        result = subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--corrections",
                "--path",
                str(logs),
                "--out",
                str(out),
                "--dry-run",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("correction trace dry run: no files written", result.stdout)
        self.assertFalse(out.exists())
```

- [ ] **Step 3: Run the new tests and verify the missing flag fails**

Run:

```powershell
python -m unittest tests.test_corrections.CorrectionTraceTest -v
```

Expected: `FAIL` because `--corrections` is not recognized.

- [ ] **Step 4: Add stable event extraction helpers to `ditto.py`**

Extend the import line:

```python
import argparse, glob, hashlib, json, os, re, sys
```

Add after `user_messages`:

```python
def correction_session_id(path):
    normalized = os.path.normcase(os.path.abspath(path))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def correction_event_id(session_id, sequence, role, text):
    raw = f"{session_id}:{sequence}:{role}:{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def conversation_texts(content):
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    return [
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and item.get("type", "text") == "text"
    ]


def claude_conversation_events(path, no_redact=False):
    events = []
    redactions = 0
    session_id = correction_session_id(path)
    sequence = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                row_type = row.get("type")
                if row_type not in ("user", "assistant"):
                    continue
                message = row.get("message", {})
                role = message.get("role", row_type)
                if role not in ("user", "assistant"):
                    continue
                for raw_text in conversation_texts(message.get("content", "")):
                    text = (raw_text or "").strip()
                    if not text or (role == "user" and text.startswith("<")):
                        continue
                    if is_pasted_log(text):
                        continue
                    if not no_redact:
                        redacted = redact(text)
                        if redacted != text:
                            redactions += 1
                        text = redacted
                    event = {
                        "schema_version": 1,
                        "event_id": correction_event_id(session_id, sequence, role, text),
                        "session_id": session_id,
                        "sequence": sequence,
                        "timestamp": row.get("timestamp", "") or "",
                        "role": role,
                        "text": text,
                    }
                    events.append(event)
                    sequence += 1
    except Exception:
        return [], 0
    return events, redactions


def extract_correction_events(files, no_redact=False):
    events = []
    sessions = assistant_messages = redactions = 0
    for path in files:
        session_events, session_redactions = claude_conversation_events(path, no_redact)
        if not session_events:
            continue
        sessions += 1
        redactions += session_redactions
        assistant_messages += sum(event["role"] == "assistant" for event in session_events)
        events.extend(session_events)
    return {
        "events": events,
        "sessions": sessions,
        "assistant_messages": assistant_messages,
        "redactions": redactions,
    }


def write_correction_outputs(result, out_dir):
    correction_dir = os.path.join(out_dir, "corrections")
    os.makedirs(correction_dir, exist_ok=True)
    events_path = os.path.join(correction_dir, "events.jsonl")
    with open(events_path, "w", encoding="utf-8") as fh:
        for event in result["events"]:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    stats = {
        "schema_version": 1,
        "sessions": result["sessions"],
        "events": len(result["events"]),
        "assistant_messages": result["assistant_messages"],
        "redactions": result["redactions"],
    }
    with open(os.path.join(correction_dir, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)
    return events_path
```

- [ ] **Step 5: Add the opt-in CLI branch before normal profile extraction**

Add the argument:

```python
ap.add_argument(
    "--corrections",
    action="store_true",
    help="opt in to a Claude-only user+assistant correction trace",
)
```

Add this branch after card/install handling and before normal `roots` selection:

```python
if args.corrections:
    if not args.path and args.source not in ("auto", "claude"):
        print("correction traces currently support Claude Code only. use --source claude or --path.")
        sys.exit(1)
    roots = [args.path] if args.path else SOURCES["claude"]
    files = discover_files(roots)
    if not files:
        print("no Claude JSONL logs found for correction extraction.")
        sys.exit(1)
    result = extract_correction_events(files, args.no_redact)
    print("correction trace is opt-in and includes assistant conversation text")
    print(f"sessions: {result['sessions']}")
    print(f"events: {len(result['events'])}")
    print(f"assistant messages included: {result['assistant_messages']}")
    print(f"secrets/PII redacted: {result['redactions']}")
    if args.dry_run:
        print("correction trace dry run: no files written")
        return
    events_path = write_correction_outputs(result, args.out)
    print(f"wrote private correction trace: {events_path}")
    print("next: use CORRECTION_PROMPT.md to create corrections/candidates.json")
    return
```

- [ ] **Step 6: Run the correction tests and full suite**

```powershell
python -m unittest tests.test_corrections.CorrectionTraceTest -v
python -m unittest discover -s tests -v
```

Expected: both correction tests pass and the original 9 tests still pass.

- [ ] **Step 7: Commit the opt-in trace extractor**

```powershell
git add ditto.py tests/test_corrections.py
git commit -m "feat: extract opt-in Claude correction traces"
```

**Done means:** default Ditto still keeps assistant text out; `--corrections` explicitly includes only redacted Claude user/assistant conversational text; tool/thinking blocks and source paths are absent; dry-run writes nothing.

---

### Move 3, Days 5-6: Require machine-verifiable correction receipts

**Files:**
- Modify: `ditto.py`
- Modify: `tests/test_corrections.py`
- Create: `CORRECTION_PROMPT.md`

- [ ] **Step 1: Add direct-import helpers and failing receipt-validation tests**

Add these imports and loader to `tests/test_corrections.py`:

```python
import importlib.util


SPEC = importlib.util.spec_from_file_location("ditto_module", DITTO)
DITTO_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DITTO_MODULE)
```

Add:

```python
class CorrectionReceiptTest(unittest.TestCase):
    def make_events(self):
        events = []
        for index, session_id in enumerate(("session-a", "session-b")):
            events.extend([
                {
                    "event_id": f"request-{index}",
                    "session_id": session_id,
                    "sequence": 0,
                    "timestamp": f"2026-07-0{index + 1}T10:00:00Z",
                    "role": "user",
                    "text": "ship the fix",
                },
                {
                    "event_id": f"assistant-{index}",
                    "session_id": session_id,
                    "sequence": 1,
                    "timestamp": f"2026-07-0{index + 1}T10:01:00Z",
                    "role": "assistant",
                    "text": "I edited the file.",
                },
                {
                    "event_id": f"correction-{index}",
                    "session_id": session_id,
                    "sequence": 2,
                    "timestamp": f"2026-07-0{index + 1}T10:02:00Z",
                    "role": "user",
                    "text": "open production and prove it",
                },
            ])
        return events

    def candidate(self):
        return {
            "id": "live-proof-before-done",
            "summary": "The user rejects done without live proof.",
            "proposed_rule": "Do not claim done until the running product is verified.",
            "receipts": [
                {
                    "request_event_id": "request-0",
                    "assistant_event_id": "assistant-0",
                    "correction_event_id": "correction-0",
                },
                {
                    "request_event_id": "request-1",
                    "assistant_event_id": "assistant-1",
                    "correction_event_id": "correction-1",
                },
            ],
        }

    def test_candidate_requires_two_valid_session_receipts(self):
        validated = DITTO_MODULE.validate_correction_candidate(self.candidate(), self.make_events())
        self.assertEqual(validated["receipt_session_count"], 2)

    def test_candidate_rejects_an_invented_event_id(self):
        candidate = self.candidate()
        candidate["receipts"][1]["correction_event_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "unknown event id"):
            DITTO_MODULE.validate_correction_candidate(candidate, self.make_events())

    def test_candidate_rejects_two_receipts_from_one_session(self):
        events = self.make_events()[:3]
        candidate = self.candidate()
        candidate["receipts"][1] = dict(candidate["receipts"][0])
        with self.assertRaisesRegex(ValueError, "two separate sessions"):
            DITTO_MODULE.validate_correction_candidate(candidate, events)
```

- [ ] **Step 2: Run the receipt tests and verify the validator is missing**

```powershell
python -m unittest tests.test_corrections.CorrectionReceiptTest -v
```

Expected: `ERROR` because `validate_correction_candidate` does not exist.

- [ ] **Step 3: Add deterministic receipt validation to `ditto.py`**

Add:

```python
CORRECTION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")


def event_index(events):
    return {event["event_id"]: event for event in events}


def validate_correction_receipt(receipt, events_by_id):
    keys = ("request_event_id", "assistant_event_id", "correction_event_id")
    try:
        request, assistant, correction = [events_by_id[receipt[key]] for key in keys]
    except KeyError as exc:
        raise ValueError(f"unknown event id: {exc.args[0]}") from exc
    if not (request["session_id"] == assistant["session_id"] == correction["session_id"]):
        raise ValueError("receipt events must come from one session")
    if [request["role"], assistant["role"], correction["role"]] != ["user", "assistant", "user"]:
        raise ValueError("receipt roles must be user, assistant, user")
    if not (request["sequence"] < assistant["sequence"] < correction["sequence"]):
        raise ValueError("receipt events must be in request, assistant, correction order")
    return request["session_id"]


def validate_correction_candidate(candidate, events):
    candidate_id = candidate.get("id", "")
    if not CORRECTION_ID_RE.fullmatch(candidate_id):
        raise ValueError(f"invalid correction id: {candidate_id}")
    if not candidate.get("summary", "").strip():
        raise ValueError(f"candidate {candidate_id} has no summary")
    if not candidate.get("proposed_rule", "").strip():
        raise ValueError(f"candidate {candidate_id} has no proposed rule")
    receipts = candidate.get("receipts", [])
    if len(receipts) < 2:
        raise ValueError(f"candidate {candidate_id} needs at least two receipts")
    events_by_id = event_index(events)
    sessions = {
        validate_correction_receipt(receipt, events_by_id)
        for receipt in receipts
    }
    if len(sessions) < 2:
        raise ValueError(f"candidate {candidate_id} needs receipts from two separate sessions")
    validated = dict(candidate)
    validated["receipt_session_count"] = len(sessions)
    return validated
```

- [ ] **Step 4: Run the receipt tests**

```powershell
python -m unittest tests.test_corrections.CorrectionReceiptTest -v
```

Expected: all three tests pass.

- [ ] **Step 5: Create the exact candidate-mining prompt**

Create `CORRECTION_PROMPT.md` with:

````markdown
# Ditto correction candidate pass

Read `ditto-out/corrections/events.jsonl`. It is private, redacted conversation text from an explicit opt-in run.

Find repeated explicit correction chains only:

1. a user request,
2. the assistant behavior that failed the user's intent,
3. an explicit user correction.

Hard rules:

- Keep a candidate only when the same behavioral correction has receipts from at least two separate sessions.
- Never treat silence, continued conversation, a later success, or lack of another complaint as approval.
- Do not infer tool results or file contents that are absent from the event stream.
- Every receipt must reference real event IDs in request -> assistant -> correction order from one session.
- The proposed rule must be specific, imperative, and observable. It must tell an agent what to do differently.
- Do not quote full logs. The JSON contains IDs, a short summary, and the proposed rule only.
- If no candidate satisfies the contract, write an empty `candidates` list.

Write only valid JSON to `ditto-out/corrections/candidates.json`:

```json
{
  "schema_version": 1,
  "candidates": [
    {
      "id": "live-proof-before-done",
      "summary": "The user repeatedly rejects completion claims without live verification.",
      "proposed_rule": "Do not claim work is done until the running product is checked and the result is shown.",
      "receipts": [
        {
          "request_event_id": "7a2d0b3c4e5f6789",
          "assistant_event_id": "8b3e1c4d5f607182",
          "correction_event_id": "9c4f2d5e60718293"
        },
        {
          "request_event_id": "ad503e6f718293a4",
          "assistant_event_id": "be614f728394a5b6",
          "correction_event_id": "cf72508394a5b6c7"
        }
      ]
    }
  ]
}
```

The example shows the required shape. Every emitted value must come from the actual event file.
````

- [ ] **Step 6: Run the full suite and commit the receipt contract**

```powershell
python -m unittest discover -s tests -v
git add ditto.py tests/test_corrections.py CORRECTION_PROMPT.md
git commit -m "feat: require evidence-backed correction candidates"
```

**Done means:** an agent can propose candidates, but invented IDs, wrong sequence, wrong roles, one-session repetition, and inference from silence cannot enter the product ledger.

---

### Move 4, Days 7-9: Build the approval ledger and separate correction skill

**Files:**
- Modify: `ditto.py`
- Modify: `tests/test_corrections.py`
- Create: `schemas/ditto-correction-ledger-v1.schema.json`

- [ ] **Step 1: Add a failing end-to-end approval test**

Add this helper to `tests/test_corrections.py`:

```python
def write_events(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event) + "\n")
```

Add to `CorrectionReceiptTest`:

```python
def test_review_approves_candidate_and_renders_separate_skill(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        correction_dir = root / "corrections"
        events_path = correction_dir / "events.jsonl"
        candidates_path = correction_dir / "candidates.json"
        write_events(events_path, self.make_events())
        candidates_path.write_text(
            json.dumps({"schema_version": 1, "candidates": [self.candidate()]}),
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--review-corrections",
                str(candidates_path),
                "--events",
                str(events_path),
            ],
            input="a\n",
            check=True,
            capture_output=True,
            text=True,
        )

        ledger = json.loads((correction_dir / "ledger.json").read_text(encoding="utf-8"))
        skill = (correction_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(ledger["corrections"][0]["status"], "approved")
        self.assertEqual(ledger["corrections"][0]["receipt_session_count"], 2)
        self.assertIn("name: ditto-corrections", skill)
        self.assertIn("Do not claim done until the running product is verified.", skill)
        self.assertNotIn("ship the fix", skill)
        self.assertIn("wrote approved correction skill", result.stdout)
```

- [ ] **Step 2: Add failing edit and forged-candidate tests**

Add:

```python
def test_review_allows_user_to_edit_before_approval(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        correction_dir = root / "corrections"
        events_path = correction_dir / "events.jsonl"
        candidates_path = correction_dir / "candidates.json"
        write_events(events_path, self.make_events())
        candidates_path.write_text(
            json.dumps({"schema_version": 1, "candidates": [self.candidate()]}),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--review-corrections",
                str(candidates_path),
                "--events",
                str(events_path),
            ],
            input="e\nVerify the deployed URL before saying done.\n",
            check=True,
            capture_output=True,
            text=True,
        )
        skill = (correction_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Verify the deployed URL before saying done.", skill)

def test_review_rejects_forged_candidate_before_prompting(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        correction_dir = root / "corrections"
        events_path = correction_dir / "events.jsonl"
        candidates_path = correction_dir / "candidates.json"
        write_events(events_path, self.make_events())
        candidate = self.candidate()
        candidate["receipts"][0]["assistant_event_id"] = "invented"
        candidates_path.write_text(
            json.dumps({"schema_version": 1, "candidates": [candidate]}),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--review-corrections",
                str(candidates_path),
                "--events",
                str(events_path),
            ],
            input="a\n",
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown event id", result.stdout)
        self.assertFalse((correction_dir / "ledger.json").exists())
```

- [ ] **Step 3: Run the three review tests and verify the CLI is missing**

```powershell
python -m unittest tests.test_corrections.CorrectionReceiptTest.test_review_approves_candidate_and_renders_separate_skill tests.test_corrections.CorrectionReceiptTest.test_review_allows_user_to_edit_before_approval tests.test_corrections.CorrectionReceiptTest.test_review_rejects_forged_candidate_before_prompting -v
```

Expected: failure because `--review-corrections` is not recognized.

- [ ] **Step 4: Add ledger loading, receipt display, approval, and skill rendering**

Extend imports:

```python
from datetime import datetime, timezone
```

Add:

```python
def read_json_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return json.load(fh)


def read_event_file(path):
    events = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip():
                events.append(json.loads(line))
    return events


def clipped(text, limit=160):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def render_correction_skill(corrections):
    approved = [item for item in corrections if item.get("status") == "approved"]
    lines = [
        "---",
        "name: ditto-corrections",
        "description: User-approved corrections backed by repeated explicit AI-session evidence.",
        "---",
        "",
        "# Ditto corrections",
        "",
        "Apply these user-approved rules before implementation and verification.",
        "A current direct user instruction always wins if it conflicts with this file.",
        "",
    ]
    for item in approved:
        lines.append(
            f"- [{item['id']}] {item['rule']} "
            f"({item['receipt_session_count']} sessions)"
        )
    return "\n".join(lines).rstrip() + "\n"


def review_correction_candidates(candidates_path, events_path, input_fn=input):
    bundle = read_json_file(candidates_path)
    if bundle.get("schema_version") != 1:
        raise ValueError("unsupported candidate schema version")
    events = read_event_file(events_path)
    events_by_id = event_index(events)
    validated = [
        validate_correction_candidate(candidate, events)
        for candidate in bundle.get("candidates", [])
    ]
    corrections = []
    for candidate in validated:
        print(f"\n{candidate['id']}: {candidate['summary']}")
        print(f"proposed rule: {candidate['proposed_rule']}")
        for number, receipt in enumerate(candidate["receipts"], start=1):
            request = events_by_id[receipt["request_event_id"]]
            assistant = events_by_id[receipt["assistant_event_id"]]
            correction = events_by_id[receipt["correction_event_id"]]
            print(f"receipt {number} request: {clipped(request['text'])}")
            print(f"receipt {number} assistant: {clipped(assistant['text'])}")
            print(f"receipt {number} correction: {clipped(correction['text'])}")
        choice = input_fn("[a]pprove, [e]dit, [r]eject, [s]kip: ").strip().lower()
        rule = candidate["proposed_rule"].strip()
        status = "approved"
        if choice == "e":
            rule = input_fn("approved rule: ").strip()
            if not rule:
                raise ValueError("edited rule cannot be empty")
        elif choice == "r":
            status = "rejected"
            rule = ""
        elif choice == "s":
            continue
        elif choice != "a":
            raise ValueError(f"unknown review choice: {choice}")
        corrections.append({
            "id": candidate["id"],
            "status": status,
            "summary": candidate["summary"],
            "rule": rule,
            "receipt_session_count": candidate["receipt_session_count"],
            "receipts": candidate["receipts"],
            "approved_at": now_utc() if status == "approved" else "",
            "reviews": [],
        })
    reviewed_through = max((event.get("timestamp", "") for event in events), default="")
    ledger = {
        "schema_version": 1,
        "reviewed_through": reviewed_through,
        "corrections": corrections,
    }
    correction_dir = os.path.dirname(os.path.abspath(candidates_path))
    ledger_path = os.path.join(correction_dir, "ledger.json")
    with open(ledger_path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
    approved = [item for item in corrections if item["status"] == "approved"]
    if approved:
        skill_path = os.path.join(correction_dir, "SKILL.md")
        with open(skill_path, "w", encoding="utf-8") as fh:
            fh.write(render_correction_skill(corrections))
        print(f"wrote approved correction skill: {skill_path}")
    print(f"wrote correction ledger: {ledger_path}")
    return ledger
```

Wrap the CLI call in `try/except ValueError` so invalid agent output exits nonzero with the exact validation message:

```python
try:
    review_correction_candidates(candidates_path, events_path)
except (OSError, ValueError, json.JSONDecodeError) as exc:
    print(f"correction review failed: {exc}")
    sys.exit(1)
```

- [ ] **Step 5: Add CLI arguments and routing for review**

Add:

```python
ap.add_argument(
    "--review-corrections",
    nargs="?",
    const="",
    metavar="CANDIDATES_JSON",
    help="validate and approve/edit/reject correction candidates",
)
ap.add_argument("--events", help="correction events JSONL used to validate receipts")
```

Route before extraction:

```python
if args.review_corrections is not None:
    candidates_path = args.review_corrections or os.path.join(
        args.out, "corrections", "candidates.json"
    )
    events_path = args.events or os.path.join(args.out, "corrections", "events.jsonl")
    try:
        review_correction_candidates(candidates_path, events_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"correction review failed: {exc}")
        sys.exit(1)
    return
```

- [ ] **Step 6: Run review tests**

```powershell
python -m unittest tests.test_corrections.CorrectionReceiptTest -v
```

Expected: receipt, approval, edit, and forged-evidence tests pass.

- [ ] **Step 7: Add named installs without changing existing destinations**

Add a failing test to `tests/test_ditto.py`:

```python
def test_install_named_claude_skill_keeps_you_profile_separate(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home"
        skill = root / "SKILL.md"
        skill.write_text(
            "---\nname: ditto-corrections\ndescription: approved corrections\n---\n\n# rules\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--install",
                str(skill),
                "--target",
                "claude",
                "--skill-name",
                "ditto-corrections",
                "--home",
                str(home),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertTrue((home / ".claude" / "skills" / "ditto-corrections" / "SKILL.md").exists())
        self.assertFalse((home / ".claude" / "skills" / "you" / "SKILL.md").exists())
```

Run it and verify `--skill-name` is unrecognized:

```powershell
python -m unittest tests.test_ditto.DittoCliTest.test_install_named_claude_skill_keeps_you_profile_separate -v
```

Then add:

```python
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def validate_skill_name(skill_name):
    if not SKILL_NAME_RE.fullmatch(skill_name):
        raise ValueError(f"invalid skill name: {skill_name}")
    return skill_name
```

Replace `install_destination` with the complete named-destination implementation:

```python
def install_destination(target, repo_dir, home_dir, skill_name="you"):
    skill_name = validate_skill_name(skill_name)
    if target == "claude":
        return os.path.join(home_dir, ".claude", "skills", skill_name, "SKILL.md")
    if target == "codex":
        return os.path.join(home_dir, ".codex", "skills", skill_name, "SKILL.md")
    if target == "cursor":
        return os.path.join(repo_dir, ".cursor", "rules", f"{skill_name}.mdc")
    if skill_name != "you":
        raise ValueError(f"named installs are not supported for target: {target}")
    if target == "agents":
        return os.path.join(repo_dir, "AGENTS.md")
    if target == "gemini":
        return os.path.join(repo_dir, "GEMINI.md")
    raise ValueError(f"unknown target: {target}")
```

Change the installer signature and destination call:

```python
def install_profile(
    profile_path,
    target,
    repo_dir,
    home_dir,
    yes=False,
    dry_run=False,
    skill_name="you",
):
    # Keep the existing body, but call:
    dest = install_destination(target, repo_dir, home_dir, skill_name)
```

Add the CLI argument:

```python
ap.add_argument("--skill-name", default="you", help="install name for Claude/Codex/Cursor skills")
```

Replace the existing installer call in `main` with:

```python
install_profile(
    args.install,
    args.target,
    args.repo,
    args.home,
    args.yes,
    args.dry_run,
    args.skill_name,
)
```

The `install_destination` guard above preserves the existing fixed marked block for `AGENTS.md` and `GEMINI.md` and rejects other names for those targets.

- [ ] **Step 8: Publish the ledger v1 schema**

Create `schemas/ditto-correction-ledger-v1.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/ohad6k/ditto/schemas/ditto-correction-ledger-v1.schema.json",
  "title": "Ditto correction ledger v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "reviewed_through", "corrections"],
  "properties": {
    "schema_version": {"const": 1},
    "reviewed_through": {"type": "string"},
    "corrections": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "id",
          "status",
          "summary",
          "rule",
          "receipt_session_count",
          "receipts",
          "approved_at",
          "reviews"
        ],
        "properties": {
          "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,63}$"},
          "status": {"enum": ["approved", "rejected"]},
          "summary": {"type": "string"},
          "rule": {"type": "string"},
          "receipt_session_count": {"type": "integer", "minimum": 2},
          "receipts": {
            "type": "array",
            "minItems": 2,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["request_event_id", "assistant_event_id", "correction_event_id"],
              "properties": {
                "request_event_id": {"type": "string", "minLength": 1},
                "assistant_event_id": {"type": "string", "minLength": 1},
                "correction_event_id": {"type": "string", "minLength": 1}
              }
            }
          },
          "approved_at": {"type": "string"},
          "reviews": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "reviewed_at",
                "result",
                "reason",
                "request_event_id",
                "assistant_event_id",
                "correction_event_id"
              ],
              "properties": {
                "reviewed_at": {"type": "string"},
                "result": {"enum": ["recurred", "dismissed", "no_evidence", "unclear"]},
                "reason": {"type": "string"},
                "request_event_id": {"type": "string"},
                "assistant_event_id": {"type": "string"},
                "correction_event_id": {"type": "string"}
              }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 9: Run the full suite and commit**

```powershell
python -m unittest discover -s tests -v
git add ditto.py tests/test_ditto.py tests/test_corrections.py schemas/ditto-correction-ledger-v1.schema.json
git commit -m "feat: approve corrections into a portable skill ledger"
```

**Done means:** a real two-session correction can be approved or edited, forged evidence is blocked, `ledger.json` is machine-readable, `SKILL.md` is lean, and installation does not overwrite the user's existing `you` skill.

---

### Move 5, Days 10-11: Create the weekly return loop

**Files:**
- Modify: `ditto.py`
- Modify: `tests/test_corrections.py`
- Create: `CORRECTION_REVIEW_PROMPT.md`

- [ ] **Step 1: Add a failing delta-extraction test**

Add to `CorrectionTraceTest`:

```python
def test_since_ledger_writes_only_new_events(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        logs = root / "logs"
        out = root / "ditto-out"
        write_jsonl(logs / "old.jsonl", claude_rows(1))
        write_jsonl(logs / "new.jsonl", claude_rows(10))
        correction_dir = out / "corrections"
        correction_dir.mkdir(parents=True)
        ledger = correction_dir / "ledger.json"
        ledger.write_text(
            json.dumps({
                "schema_version": 1,
                "reviewed_through": "2026-07-05T00:00:00Z",
                "corrections": [],
            }),
            encoding="utf-8",
        )

        subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--corrections",
                "--path",
                str(logs),
                "--out",
                str(out),
                "--since-ledger",
                str(ledger),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        events = [
            json.loads(line)
            for line in (correction_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(events)
        self.assertTrue(all(event["timestamp"] > "2026-07-05T00:00:00Z" for event in events))
```

- [ ] **Step 2: Run the delta test and verify the flag is missing**

```powershell
python -m unittest tests.test_corrections.CorrectionTraceTest.test_since_ledger_writes_only_new_events -v
```

Expected: failure because `--since-ledger` is not recognized.

- [ ] **Step 3: Add ledger-cursor filtering**

Add:

```python
def filter_events_after(events, reviewed_through):
    if not reviewed_through:
        return events
    return [event for event in events if event.get("timestamp", "") > reviewed_through]
```

Add the argument:

```python
ap.add_argument("--since-ledger", metavar="LEDGER_JSON", help="with --corrections, keep events newer than the ledger cursor")
```

In the correction extraction branch, after `extract_correction_events`:

```python
if args.since_ledger:
    ledger = read_json_file(args.since_ledger)
    result["events"] = filter_events_after(
        result["events"], ledger.get("reviewed_through", "")
    )
    result["sessions"] = len({
        event["session_id"] for event in result["events"]
    })
    result["assistant_messages"] = sum(
        event["role"] == "assistant" for event in result["events"]
    )
```

- [ ] **Step 4: Create the recurrence-mining prompt**

Create `CORRECTION_REVIEW_PROMPT.md`:

````markdown
# Ditto weekly correction review

Read:

- `ditto-out/corrections/ledger.json`
- the new-only `ditto-out/corrections/events.jsonl`

For each approved correction, look only for a new explicit recurrence chain. A recurrence requires a user request, an assistant behavior that violates the approved rule, and an explicit user correction.

Hard rules:

- No complaint is not proof that the rule held.
- Silence, task completion, and continued conversation are not success signals.
- Use `recurred` only with real new event IDs.
- Use `no_evidence` when no explicit recurrence chain is present. This means unknown, not success.
- Use `unclear` when an event might be related but does not establish the chain.
- Do not revise the installed rule automatically.

Write only JSON to `ditto-out/corrections/review.json`:

```json
{
  "schema_version": 1,
  "checks": [
    {
      "correction_id": "live-proof-before-done",
      "result": "recurred",
      "reason": "The assistant again claimed completion before live verification and the user explicitly corrected it.",
      "request_event_id": "7a2d0b3c4e5f6789",
      "assistant_event_id": "8b3e1c4d5f607182",
      "correction_event_id": "9c4f2d5e60718293"
    }
  ]
}
```

Allowed results are `recurred`, `no_evidence`, and `unclear`. For `no_evidence`, event IDs must be empty strings.
````

- [ ] **Step 5: Add a failing confirmed-recurrence test**

Add a test that creates a v1 ledger with one approved correction, writes a three-event recurrence chain, writes `review.json`, runs the apply command with `input="y\n"`, and asserts the ledger receives one review:

```python
def test_apply_recurrence_review_requires_user_confirmation(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        correction_dir = root / "corrections"
        events = CorrectionReceiptTest().make_events()[:3]
        events_path = correction_dir / "events.jsonl"
        write_events(events_path, events)
        ledger_path = correction_dir / "ledger.json"
        ledger_path.write_text(json.dumps({
            "schema_version": 1,
            "reviewed_through": "2026-07-01T00:00:00Z",
            "corrections": [{
                "id": "live-proof-before-done",
                "status": "approved",
                "summary": "Live proof is required.",
                "rule": "Verify the running product before saying done.",
                "receipt_session_count": 2,
                "receipts": [
                    {
                        "request_event_id": "old-request-a",
                        "assistant_event_id": "old-assistant-a",
                        "correction_event_id": "old-correction-a",
                    },
                    {
                        "request_event_id": "old-request-b",
                        "assistant_event_id": "old-assistant-b",
                        "correction_event_id": "old-correction-b",
                    },
                ],
                "approved_at": "2026-07-01T00:00:00+00:00",
                "reviews": [],
            }],
        }), encoding="utf-8")
        review_path = correction_dir / "review.json"
        review_path.write_text(json.dumps({
            "schema_version": 1,
            "checks": [{
                "correction_id": "live-proof-before-done",
                "result": "recurred",
                "reason": "Explicit correction repeated.",
                "request_event_id": "request-0",
                "assistant_event_id": "assistant-0",
                "correction_event_id": "correction-0",
            }],
        }), encoding="utf-8")

        subprocess.run(
            [
                sys.executable,
                str(DITTO),
                "--apply-correction-review",
                str(review_path),
                "--events",
                str(events_path),
                "--ledger",
                str(ledger_path),
            ],
            input="y\n",
            check=True,
            capture_output=True,
            text=True,
        )

        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(ledger["corrections"][0]["reviews"][0]["result"], "recurred")
        self.assertEqual(ledger["reviewed_through"], "2026-07-01T10:02:00Z")
```

- [ ] **Step 6: Implement recurrence validation and application**

Add:

```python
def apply_correction_review(review_path, events_path, ledger_path, input_fn=input):
    review = read_json_file(review_path)
    ledger = read_json_file(ledger_path)
    events = read_event_file(events_path)
    events_by_id = event_index(events)
    corrections = {item["id"]: item for item in ledger.get("corrections", [])}
    if review.get("schema_version") != 1 or ledger.get("schema_version") != 1:
        raise ValueError("unsupported correction review or ledger schema")
    for check in review.get("checks", []):
        correction_id = check.get("correction_id", "")
        if correction_id not in corrections or corrections[correction_id].get("status") != "approved":
            raise ValueError(f"unknown approved correction: {correction_id}")
        result = check.get("result")
        if result not in ("recurred", "no_evidence", "unclear"):
            raise ValueError(f"invalid recurrence result: {result}")
        if result == "recurred":
            receipt = {
                "request_event_id": check.get("request_event_id", ""),
                "assistant_event_id": check.get("assistant_event_id", ""),
                "correction_event_id": check.get("correction_event_id", ""),
            }
            validate_correction_receipt(receipt, events_by_id)
            confirmed = input_fn(
                f"confirm recurrence for {correction_id}? [y/N]: "
            ).strip().lower() == "y"
            stored_result = "recurred" if confirmed else "dismissed"
        else:
            if any(check.get(key) for key in (
                "request_event_id", "assistant_event_id", "correction_event_id"
            )):
                raise ValueError(f"{result} must not claim receipt event ids")
            stored_result = result
        corrections[correction_id].setdefault("reviews", []).append({
            "reviewed_at": now_utc(),
            "result": stored_result,
            "reason": check.get("reason", ""),
            "request_event_id": check.get("request_event_id", ""),
            "assistant_event_id": check.get("assistant_event_id", ""),
            "correction_event_id": check.get("correction_event_id", ""),
        })
    cursor_values = [ledger.get("reviewed_through", "")]
    cursor_values.extend(event.get("timestamp", "") for event in events)
    cursor_values = [value for value in cursor_values if value]
    if cursor_values:
        ledger["reviewed_through"] = max(cursor_values)
    with open(ledger_path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
    print(f"updated correction ledger: {ledger_path}")
    return ledger
```

Add arguments and route them before extraction:

```python
ap.add_argument("--apply-correction-review", metavar="REVIEW_JSON", help="validate and record a weekly recurrence review")
ap.add_argument("--ledger", metavar="LEDGER_JSON", help="correction ledger path")
```

Add this handler before the `--review-corrections` and `--corrections` branches:

```python
if args.apply_correction_review:
    if not args.events or not args.ledger:
        print("--apply-correction-review requires --events and --ledger")
        sys.exit(1)
    try:
        apply_correction_review(
            args.apply_correction_review,
            args.events,
            args.ledger,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"correction recurrence review failed: {exc}")
        sys.exit(1)
    return
```

- [ ] **Step 7: Run delta, recurrence, and full suites**

```powershell
python -m unittest tests.test_corrections -v
python -m unittest discover -s tests -v
```

Expected: all tests pass. The weekly review never records `held`; `no_evidence` remains explicitly unknown.

- [ ] **Step 8: Commit the weekly loop**

```powershell
git add ditto.py tests/test_corrections.py CORRECTION_REVIEW_PROMPT.md
git commit -m "feat: review new sessions for correction recurrence"
```

**Done means:** rerunning Ditto after new work produces a smaller private trace, approved corrections are checked for explicit recurrence, and every recurrence remains human-confirmed.

---

### Move 6, Days 12-14: Dogfood, benchmark, document, and enforce the gate

**Files:**
- Create: `docs/experiments/correction-benchmark.md`
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `SECURITY.md`
- Modify: `skills/ditto/SKILL.md`

- [ ] **Step 1: Write the exact blinded benchmark protocol**

Create `docs/experiments/correction-benchmark.md` with:

```markdown
# Ditto Correction Benchmark

## Question

Does one user-approved correction skill reduce the need for that same correction on held-out tasks?

## Frozen setup

- Claude Code only.
- One fixed Claude model/version for every run.
- Same permissions, tools, repository snapshot, and task prompt for both variants.
- Six held-out tasks where the target correction is relevant but the two receipt sessions are excluded.
- Variant A loads the current user-only Ditto profile.
- Variant B loads the same profile plus the approved `ditto-corrections` skill.
- A crew member randomizes A/B order and removes variant labels before Ohad judges.

## Judge form

For every output, Ohad records only:

- `target_correction_needed`: yes or no
- `severe_regression`: yes or no
- one short reason

Do not use an LLM judge for the primary result.

## Pass gate

Variant B must receive strictly fewer `target_correction_needed: yes` flags than Variant A.
A tie fails. Any severe regression in Variant B fails the gate.

## Retention gate

After at least two new real work sessions, rerun the new-only extraction and complete a correction review through the product. Merely opening the ledger file does not count.

## Stop rule

If the benchmark or retention gate fails, do not expand to more sources, background hooks, workflow mining, or profile versioning. Record the failure mode and repair only the narrow loop.
```

- [ ] **Step 2: Dogfood one real correction through the product**

Run:

```powershell
python ditto.py --corrections --source claude --out ditto-out
```

Use `CORRECTION_PROMPT.md` to write `ditto-out/corrections/candidates.json`, then run:

```powershell
python ditto.py --review-corrections --out ditto-out
python ditto.py --install ditto-out/corrections/SKILL.md --target claude --skill-name ditto-corrections
```

Verify in a new Claude Code session that `ditto-corrections` is registered before running the benchmark. Record the exact candidate ID, two session receipts, user decision, and installed path in a private experiment note outside the repository. Do not commit real traces, the real ledger, or the generated personal skill.

- [ ] **Step 3: Run the six-task benchmark and record the result**

Follow `docs/experiments/correction-benchmark.md`. Freeze all prompts before the first run. Have a crew member randomize and blind the outputs. Ohad judges every pair without seeing variant labels.

Expected pass result: Variant B has fewer target-correction flags, zero severe regressions, and the result is reproducible from the frozen task set.

- [ ] **Step 4: Complete the second real product review**

After at least two new work sessions:

```powershell
python ditto.py --corrections --source claude --out ditto-out --since-ledger ditto-out/corrections/ledger.json
```

Use `CORRECTION_REVIEW_PROMPT.md` to write `review.json`, then run:

```powershell
python ditto.py --apply-correction-review ditto-out/corrections/review.json --events ditto-out/corrections/events.jsonl --ledger ditto-out/corrections/ledger.json
```

This step passes only when the review is completed through the CLI. `no_evidence` is allowed but must not be described as proof that the rule worked.

- [ ] **Step 5: Add an experimental README section with exact commands and limits**

Add a section titled `Experimental: never correct the same agent twice` after the normal install instructions. Include:

```markdown
The normal Ditto profile reads only what you wrote. The experimental correction loop is a separate opt-in mode for Claude Code. It includes redacted assistant conversation text so Ditto can link a request, an assistant behavior, and your explicit correction.

It does not read tool results or tool calls. It does not silently change your profile. A candidate needs receipts from two sessions, and nothing is installed until you approve or edit the rule.
```

Show the extraction, review, named install, new-only rerun, and recurrence commands from Steps 2 and 4. State that the feature is Claude Code-only during the experiment.

- [ ] **Step 6: Update security documentation for the new opt-in boundary**

Add these exact writes:

```markdown
- `ditto-out/corrections/events.jsonl`: private redacted user and assistant conversation text
- `ditto-out/corrections/stats.json`: correction extraction counts
- `ditto-out/corrections/candidates.json`: agent-proposed candidate IDs and receipt IDs
- `ditto-out/corrections/ledger.json`: user decisions, approved rules, receipt IDs, and review history
- `ditto-out/corrections/SKILL.md`: approved rules only
```

State clearly:

```markdown
Assistant conversation text can contain generated code, file paths, project names, or other private details even when tool results are excluded. Redaction is best-effort. Keep the correction directory private and review it before using a remote model/provider or sharing any artifact. Only the approved skill and ledger format are intended for downstream consumption; neither is automatically safe to publish.
```

- [ ] **Step 7: Update the built-in Ditto skill to orchestrate the loop**

Add a section to `skills/ditto/SKILL.md` that instructs the agent to:

1. Explain the opt-in assistant-text boundary and request confirmation before `--corrections`.
2. Run correction extraction with `--dry-run` first.
3. Use `CORRECTION_PROMPT.md` and write only the candidate JSON contract.
4. Run the CLI validator/reviewer; never approve on the user's behalf.
5. Install the separate named skill only after approval.
6. On a later user-requested review, extract since the ledger, use `CORRECTION_REVIEW_PROMPT.md`, and run the recurrence-review CLI.
7. Never call `no_evidence` success and never post or commit the private trace.

- [ ] **Step 8: Reorder the roadmap around retention evidence**

Put `Personal Correction Ledger (experimental)` first. State that profile `--diff` is next only after the correction gate because it creates a scheduled return without expanding private trace scope. Keep workflow mining, elicitation, more sources, and counterweights under a clearly labeled post-gate section.

- [ ] **Step 9: Run final verification**

Run:

```powershell
python -m unittest discover -s tests -v
python ditto.py --help
git diff --check
rg -n "privacy-safe|100x|proves|automatic sync|always works" README.md ROADMAP.md SECURITY.md skills/ditto/SKILL.md
```

Expected:

- All tests pass.
- Help lists correction extraction, candidate review, named install, delta extraction, and recurrence review.
- `git diff --check` prints nothing.
- The claim scan prints no unsupported product promise. Contextual statements such as “the benchmark proves” must be rewritten to describe the measured result precisely.

- [ ] **Step 10: Make the release decision before publishing**

The experiment passes only when all are true:

1. Documentation matches every read and write.
2. At least one candidate has valid receipts from two separate sessions.
3. Ohad explicitly approves or edits the rule.
4. The separate correction skill installs and is visibly registered.
5. Variant B receives strictly fewer target-correction flags than Variant A with no severe regression.
6. Ohad returns for a second correction review through the product after new work.

If any condition fails, keep the feature experimental and stop expansion. If all pass, offer two opt-in external pilots; outreach still requires Ohad's approval.

- [ ] **Step 11: Commit the complete experiment**

```powershell
git add README.md ROADMAP.md SECURITY.md skills/ditto/SKILL.md docs/experiments/correction-benchmark.md
git commit -m "docs: gate ditto growth on correction-loop evidence"
```

**Done means:** Ditto has one real weekly return mechanism, one approved and separately installable behavioral patch, a machine-readable ledger for downstream tools, a blinded improvement test, and a strict stop rule.

---

## What follows only after this plan passes

Sequence the next work by retention value:

1. Profile versioning and semantic `--diff`, because it creates a scheduled monthly return while staying inside the existing user-only data boundary.
2. A documented adapter contract for tools such as Borg/Cerebro to consume `you.md` plus the correction-ledger schema.
3. Workflow mining into personal skills, after the correction ledger proves Ditto can connect behavior to explicit outcomes.
4. Additional log sources, one adapter at a time with fixtures and security documentation.
5. The elicitation pass, positioned as profile enrichment rather than the retention engine.

Do not build these as part of the 14-day correction experiment.
