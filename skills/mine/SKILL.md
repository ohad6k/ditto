---
name: mine
description: Use only when the user explicitly asks to run, set up, update, re-mine, or deepen Ditto from their real local AI coding-session history. Do not use for ordinary work, design, writing, or summarizing AGENTS.md/CLAUDE.md/rules files.
---

# Ditto mine

Mine only real user-authored `.jsonl` sessions. Never synthesize a profile from rules, memory files, or a typed self-description.

1. Locate `ditto.py` two directories above this skill; fall back to `./ditto.py` only for a direct repo checkout. Confirm Python 3 exists.
2. Store the resolved absolute runtime path as `DITTO_PY`, then run `python "$DITTO_PY" plugin preflight` with the exact mode requested by the user. Normal setup/update uses the public default candidate; `deepen work|design|write` uses `--deepen-domain`; an explicit full-history request uses `--deep`. Show valid sessions, post-dedupe source tokens, selected tokens, cache hits, planned worker calls, planned reducer calls, and the separate deep option. Do not silently change the candidate, domain, or mode.
3. For normal bounded setup/update, run `python "$DITTO_PY" plugin prepare` with the exact displayed candidate. For targeted or full deepening, show the expanded plan and wait for approval, then run `prepare` with the identical flag. Retain the exact `run_id`, `run_dir`, and assigned paths.
4. If both planned call counts are zero, run `python "$DITTO_PY" plugin activate --run-id "$RUN_ID" --cached`, then continue to step 8.
5. Spawn exactly one fast worker per uncached selected segment. Each reads the entire segment and the per-segment contract in `MINING_PROMPT.md`, writes JSON only to its assigned report path, and reads no other segment. If subagents are unavailable, process the same files sequentially without changing the count.
6. After each worker, run `python "$DITTO_PY" plugin cache-report --run-id "$RUN_ID" --report "$REPORT_PATH"`. Stop on the first rejected report.
7. Run one strongest-available reducer over only validated reports using the reducer contract. Write the complete draft pack to `pack_path`, then run `python "$DITTO_PY" plugin activate --run-id "$RUN_ID" --pack "$PACK_DIR"`.
8. Run `python "$DITTO_PY" plugin status`, retain `card_path`, then render it with `python "$DITTO_PY" --card "$CARD_PATH" --out "$RUN_DIR" --no-open`. Report the active version, domain states, selected source tokens, actual worker/reducer passes, cache reuse, card path, and targeted-deepen instruction for weak domains.

The plugin-install command itself scans no logs and schedules zero mining calls. A no-change update schedules zero additional worker/reducer calls, although the host task still has normal interaction overhead. New history gets a bounded incremental plan first. Deep mode is separately planned, resumable, redacted, and never an automatic fallback.
