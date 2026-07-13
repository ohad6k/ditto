# Ditto in OpenClaw and Hermes Agent

OpenClaw and Hermes Agent read the same skill format Ditto writes. Your mined profile is discovered by both without an adapter or any format change.

Verified 2026-07-13 on Windows with OpenClaw 2026.6.11 and Hermes Agent 0.18.2: the profile skill shows `✓ ready` in `openclaw skills list` and `enabled` in `hermes skills list`. A full live-session run is not part of this verification yet.

## Why seed them

Both runtimes learn who you are forward, session by session, starting from empty memory files. A fresh Hermes install has an empty `memories/` directory; a fresh OpenClaw agent starts blank and fills `USER.md` over weeks. Ditto already mined who you are from your real Claude Code / Codex / Copilot history, so day one can start warm.

This guide covers one direction: mined profile → runtime. Mining OpenClaw or Hermes sessions as a Ditto source is separate work, tracked in [issue #3](https://github.com/ohad6k/ditto/issues/3).

## Prerequisite

Mine your profile first (see the [Quickstart](../README.md#quickstart)). You end up with a profile skill directory, typically `~/.claude/skills/ditto/`, containing a `SKILL.md`.

## OpenClaw

Copy the profile skill into the OpenClaw workspace:

```bash
# macOS / Linux
cp -r ~/.claude/skills/ditto ~/.openclaw/workspace/skills/ditto
```

```powershell
# Windows
Copy-Item -Recurse ~\.claude\skills\ditto ~\.openclaw\workspace\skills\ditto
```

Then check:

```
openclaw skills list
```

Expect a `✓ ready` row named `ditto` with source `openclaw-workspace`.

OpenClaw also scans the shared `~/.agents/skills` directory, so if your profile already lives there it is picked up with no copying. Keep the profile in one location so a single `ditto` skill resolves.

Deeper seed (optional, from the OpenClaw bootstrapping docs, not exercised here): the workspace `USER.md` is OpenClaw's standing picture of you. You can paste your profile's core laws there before first run and start with `openclaw onboard --skip-bootstrap` so the first-run ritual does not overwrite what you seeded.

## Hermes Agent

Copy the profile skill into the Hermes skills directory:

```bash
# macOS / Linux (HERMES_HOME overrides the base directory)
cp -r ~/.claude/skills/ditto ~/.hermes/skills/ditto
```

```powershell
# Windows
Copy-Item -Recurse ~\.claude\skills\ditto $env:LOCALAPPDATA\hermes\skills\ditto
```

Then check:

```
hermes skills list
```

Expect a `ditto` row with source `local`, status `enabled`.

Deeper seed (optional): `<hermes-home>/memories/USER.md` is Hermes's always-loaded picture of you and it is capped small (about 1,375 characters per the Hermes docs). If you seed it, put only the laws that must never unload; the full profile stays in the skill.

## Naming note

There is an unrelated skill called `ditto` on ClawHub (a memory-graph tool by a different author). Installing by that name from a registry gets that project, not this one. Use the copy steps above, which install from your own mined profile.

## Privacy

The mined profile is yours and can contain how you work in detail. Copying it into another runtime's skills directory keeps it on your machine, same as Ditto's default. Publishing it anywhere is your call to make deliberately, not a step in this guide.
