---
name: mine
description: Use only when the user explicitly asks to run, set up, update, re-mine, or deepen Ditto from real local AI coding-session history.
---

# Ditto mine

Mine only real user-authored `.jsonl` sessions. Never synthesize a profile from rules files, memory, or a typed self-description.

1. Resolve `DITTO_PY` to `ditto.py` two directories above this skill, falling back to `./ditto.py` only in a direct checkout. Confirm Python 3 exists.
2. Run read-only `python "$DITTO_PY" plugin preflight`. Normal setup and updates use the bounded default candidate. Show valid sessions, post-dedupe source tokens, selected source tokens, cache hits, planned worker calls, planned reducer calls, and the separate explicit deep option.
3. Run `python "$DITTO_PY" plugin prepare` with the exact displayed candidate or approved deep mode. Retain the exact `run_id`, selected segment/report paths, and `pack_path`.
4. Run one fast worker for each uncached selected segment. Each reads only its segment and the per-segment contract in `MINING_PROMPT.md`, writes its assigned JSON report, and runs the read-only `plugin validate-report` command until accepted.
5. Cache each accepted report with `plugin cache-report`; stop on rejection.
6. Run one strongest-available reducer over only the validated reports and the combined reducer contract. It writes the complete assigned pack and self-validates with `plugin validate-pack`.
7. Activate only the validated pack with `plugin activate`, then run `plugin status` and render the card. Report active version, domain states, selected source tokens, actual worker/reducer passes, cache reuse, and targeted-deepen instructions.

Targeted or full deepening requires explicit approval of its expanded plan. Installation itself scans no logs and schedules zero mining calls. An identical update schedules zero additional Ditto mining calls, although the host task still has normal interaction overhead.

Adaptive receipt/scout stages are experimental and excluded from the Plugin release path. Run `--stage A` only when a developer explicitly requests experimental adaptive-recall testing; never select it automatically or use it for release calibration.
