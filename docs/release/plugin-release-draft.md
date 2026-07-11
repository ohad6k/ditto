# Ditto v0.2.0

Ditto is now a native Codex plugin with full-history mining as the quality default and separate personal layers for work, design, and writing.

## Install

For the cross-agent bootstrap:

```bash
npx skills add ohad6k/ditto@ditto
```

Then tell the agent `run ditto`. The bootstrap creates a read-only full-history plan, displays the exact selected source tokens and planned worker/reducer passes, and waits for approval before model work. It installs the approved core profile across supported agents; namespaced automatic routing requires the native plugin.

For native Codex routing:

```bash
codex plugin marketplace add ohad6k/ditto --ref v0.2.0 --json
codex plugin add ditto@ditto --json
```

The plugin adds `ditto:mine`, `ditto:work`, `ditto:design`, and `ditto:write`. Plugin installation itself scans no logs and schedules no mining passes.

## Full profile or quick preview

Full-history mining is the quality default. It reads all eligible history, reuses validated caches, shows the exact remaining plan, and requires cost approval before any worker or reducer runs.

Quick preview is opt-in through `run ditto quick preview` or `--preview`. Quick preview creates a starter profile from selected history, not the full profile. The widest frozen bounded calibration recovered `5/22` required traits, so this release does not present preview as equivalent to a full mine.

## Upgrade and migration

Re-run the install command to update. The `v0.2.0` skills.sh runtime is pinned to exact SHA-256 values for both `ditto.py` and `MINING_PROMPT.md`; mutable `main` bytes are not accepted.

Existing classic `you` profiles can be staged, cut over, and rolled back. Cutover moves the legacy skill out of host discovery before the new active pointer is written. The isolated release proof restored the exact legacy bytes and prior pointer state after rollback.

## Verification

- `127` unit tests, the Codex plugin validator, the bootstrap skill validator, CLI help checks, JSON parsing, and `git diff --check` pass on the local release candidate.
- Separate spec-compliance and Python safety/quality reviews both returned `PASS`.
- Codex CLI `0.142.5` discovered exactly the four native skills. Uninstall/reinstall preserved isolated private state byte-for-byte.
- A deterministic full-history fixture verified a zero-worker, zero-reducer identical update. Full-history mining has not yet been live-dogfooded on the maintainer's actual corpus in the new format; at this release-candidate stage, the full path is fixture-verified only.
- Redaction happens locally before selected text reaches the user-chosen model. `ditto.py` makes zero network calls. Runtime download and hash verification occur before log discovery.

See [the dogfood evidence](plugin-dogfood.md), [the security boundary](../../SECURITY.md), and [the roadmap](../../ROADMAP.md).

## Known limits

- A real full-history mine on the maintainer's corpus is still required before ship approval unless the release keeps the explicit fixture-only disclosure.
- Native Codex routing was not uniformly clean when an older global Ditto profile competed with the plugin.
- Native Claude plugin packaging is not claimed in this release; the skills.sh bootstrap and direct adapter remain supported.
- Benchmarks, a leaderboard, and proof/launch videos are deferred to a separate later release.

To receive future release updates on GitHub, choose **Watch -> Custom -> Releases**. A star bookmarks the repository but does not subscribe to releases.
