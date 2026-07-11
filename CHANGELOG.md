# Changelog

## 0.2.0 - 2026-07-11

### Changed

- Added the native Codex plugin with four namespaced skills: `ditto:mine`, `ditto:work`, `ditto:design`, and `ditto:write`.
- Made full-history mining the quality default. The bounded `--preview` path is explicitly a starter profile from selected history, not the full profile.
- Added deterministic segment, report, domain-draft, and reduction caches with corrupt-cache quarantine and zero-call reuse only when the cached profile is fully valid and activatable.
- Added atomic profile activation, isolated migration/cutover/rollback, and separate work, design, and writing profile routing.
- Kept adaptive recall experimental and outside the default Plugin release path.
- Added the cross-agent `npx skills add ohad6k/ditto@ditto` bootstrap. Its `v0.2.0` runtime pins `ditto.py` to SHA-256 `d4811576f65c3f6e72689b49941c4a5e405b3fbc293f56c2600d303d5ab8fa90` and `MINING_PROMPT.md` to SHA-256 `cc073f337ad6ad956bf14d60bbf6bc9d5a14d9b7f46d1be5fb2f13d62a9f4377`.

### Why it matters

Ditto can now keep setup/mining separate from the personal layers used during normal work. Full mining favors profile quality; quick preview remains available when a user knowingly prefers a bounded starter. Updates reuse validated evidence without trusting incomplete or semantically tampered cache state.

### Upgrade

Cross-agent bootstrap:

```bash
npx skills add ohad6k/ditto@ditto
```

Native Codex plugin:

```bash
codex plugin marketplace add ohad6k/ditto --ref v0.2.0 --json
codex plugin add ditto@ditto --json
```

Existing classic `you` profiles are staged and cut over through the migration commands; cutover removes the legacy skill from discovery before activating the new pointer, and rollback restores the prior bytes and pointers.

### Verified

- `127` unit tests pass on the release candidate. The Codex plugin validator and cross-agent bootstrap skill validator pass, both CLI help surfaces exit successfully, both JSON manifests parse, and `git diff --check` passes.
- Two independent read-only reviews, one for spec compliance and one for Python safety/quality, returned `PASS` on commit `328ecc61`; the final evidence record is commit `7acbcc89`.
- Codex CLI `0.142.5` discovered exactly the four native Ditto skills. Plugin uninstall/reinstall preserved an isolated private `DITTO_HOME` byte-for-byte, and isolated migration cutover/rollback restored the exact legacy state.
- The permanent frozen bounded calibration remains in `tests/fixtures/bounded-calibration-baseline.json`. Its widest candidate selected `159,919` source tokens, used three workers plus one reducer, and recovered `5/22` frozen requirements, so preview is not the quality default.
- A deterministic full-history fixture produced a validated zero-worker, zero-reducer cache hit. Full-history mining has not yet been live-dogfooded on the maintainer's actual corpus in the new format; at this release-candidate stage, the full path is fixture-verified only.
- Extraction and redaction happen locally before selected text reaches the user-chosen model. `ditto.py` makes no network calls. The skills.sh bootstrap downloads only the two pinned runtime files before log discovery and verifies both hashes.

### Known limits

- A real full-history mine on the maintainer's corpus remains a pre-ship approval gate. Unless that approved run completes and this entry is updated with its non-private proof, the full path is fixture-verified only.
- Codex native routing was proven but was not uniformly clean when an older global Ditto profile competed under the host skill-description budget. The release does not claim perfect exclusive routing in that mixed legacy environment.
- Native Claude plugin packaging is not claimed because the Claude executable was unavailable. Claude Code remains supported through the skills.sh bootstrap and direct adapter.
- Benchmarks, leaderboard results, and launch videos are deferred to a separate later release.

