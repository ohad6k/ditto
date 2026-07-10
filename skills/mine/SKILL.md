---
name: mine
description: Use only when the user explicitly asks to run, set up, update, re-mine, or deepen Ditto from real local AI coding-session history.
---

# Ditto mine

Mine only real user-authored `.jsonl` sessions. Never synthesize a profile from rules files, memory, or a typed self-description.

1. Resolve `DITTO_PY` to `ditto.py` two directories above this skill, falling back to `./ditto.py` only in a direct checkout. Confirm Python 3 exists.
2. Run read-only `python "$DITTO_PY" plugin preflight`. Show valid history, selected source tokens, exact scout and reducer calls, cache reuse, and the separate full-history option.
3. Run local-only `python "$DITTO_PY" plugin prepare --stage A`. This redacts and freezes the exact ledger, packets, hashes, and paths but makes no model call. Display that exact frozen plan, then wait for approval before starting any model work.
4. Run one fast scout for each uncached packet. Each scout reads only its assigned packet and the adaptive scout contract in `MINING_PROMPT.md`, writes its assigned JSON report, and runs the exact read-only `plugin validate-scout` command until valid.
5. Cache every accepted scout with `plugin cache-scout`. Stop on the first rejection.
6. Run the three domain reducers planned for Stage A: one each for work, design, and writing. Each reducer reads only its named evidence projection, writes one assigned draft, and runs `plugin validate-domain` until valid. Cache each with `plugin cache-domain`.
7. Run deterministic `plugin assemble --run-id "$RUN_ID"`. It performs no model call. Validate the resulting pack, then use the explicit `plugin activate` command; activation is the only profile-pointer mutation.
8. Run `plugin status`. Report the active version, domain states, exact source tokens, actual scout/reducer calls, cache reuse, card path, and any targeted next-stage instruction.

If Stage A is objectively weak, run `plugin next-stage --run-id "$RUN_ID"` to freeze a separate additional plan from the same corpus. Show its exact additional cost and wait for approval again. Never start Stage B or full-history work silently.

Plugin installation scans no logs and schedules zero mining calls. Preflight is read-only. Prepare is local-only. Do not claim a percentage of a provider subscription limit; Ditto can report only its own selected source tokens and planned calls.
