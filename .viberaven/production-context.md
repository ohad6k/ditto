# VibeRaven Production Context

## Current Release / Change Window

### 2026-07-15 - Ditto Proof v1 harness

- Change: Build a disabled-by-default benchmark harness on `codex/ditto-benchmark-proof-release`.
- Evidence: The approved design and implementation plan freeze `v0.3.7`, 24 pairs, 48 isolated cells, private fixtures outside Git, and separate execution and publication approvals.
- Boundary: This work creates local repository code and synthetic verification only. Provider/model selection, scored executions, reviewer consent, cost approval, proof clips, and publication remain later human/provider actions.
- Danger: Mixed Ditto versions, reused homes, leaked profiles or receipts, invented provider state, and public claims before complete evidence would invalidate the proof.
- Repo fix: Add the standalone `proof` package, schemas, tests, pilot fixtures, privacy gates, publication generator, and runbook without importing it from `ditto.py`.
- Verification: Baseline `python -m unittest discover -s tests -v` passed 176 tests on Python 3.11.4 before implementation.
- Provider/MCP proof: Unknown until the later live preflight captures exact provider labels, versions, argv, quotas, expected cost, and screenshots.
- Open action: Stop after the verified synthetic harness and request exact cost/run/reviewer approval before any provider execution.

## Recent Changes

## Architecture Boundaries

## Provider Boundaries

## Migration And Data History

## Incidents And Rollback Notes

## Fragile Customer Paths

## Verification Receipts

## Open Provider Or Human Actions
