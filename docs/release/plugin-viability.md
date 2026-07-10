# Ditto Plugin Host Viability

Verified on 2026-07-10 before implementation continued.

## skills.sh bootstrap

- Telemetry was disabled with `DISABLE_TELEMETRY=1`.
- `npx -y skills add <local-repository> --list` discovered the cross-agent `ditto` bootstrap separately from the temporary native spike.
- `npx -y skills add <local-repository> --skill ditto --agent codex --copy --yes` copied only `.agents/skills/ditto/SKILL.md` into the disposable audit project.
- No native-only skill was copied by the selected install.
- Decision: preserve `ohad6k/ditto@ditto` as the cross-agent bootstrap outside native plugin discovery.

## Codex native plugin

- Host: Codex CLI `0.142.5`.
- Marketplace install: `codex plugin marketplace add <local-repository> --json`.
- Plugin install: `codex plugin add ditto@ditto --json`.
- Installed identifier and version: `ditto@ditto`, `0.0.0-dev`.
- Development namespace exercised: `ditto:spike` only.
- Harmless fixture: `tests/fixtures/plugin-spike-home/spike.txt`.
- Successful fresh-task command used explicit supported model `gpt-5.4` with low reasoning effort because the user's configured `gpt-5.6-sol` requires a newer CLI:

  ```text
  codex exec -m gpt-5.4 -c model_reasoning_effort="low" --ephemeral -C <local-repository> "Use ditto:spike. Read only the DITTO_HOME path named by the skill. Return only the sentinel value."
  ```

- The task read the plugin skill, then read exactly `$env:DITTO_HOME/spike.txt` through local PowerShell. Final output: `DITTO_SPIKE_OK`.
- Invalid development attempts were not accepted as proof: the configured model was rejected before task execution, and a hidden config-directory worktree made normal sandbox access fail. The same branch was relocated to a normal worktree path before the successful proof.
- Decision: Codex native packaging, namespaced discovery, local command execution, and isolated `DITTO_HOME` access are viable. Continue the native Codex plugin architecture.

The temporary `spike` skill was removed after this proof. The relocated `.agents/skills/ditto` bootstrap is not inside the native plugin's `skills/` discovery tree.

## Claude native plugin

- `Get-Command claude -ErrorAction SilentlyContinue` returned no executable.
- Decision: native Claude packaging is not testable in this environment. No `.claude-plugin` files or native-Claude claim are included in this release. Keep the direct Claude/skills.sh adapter path.
