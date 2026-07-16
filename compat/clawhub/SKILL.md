---
name: emulo
description: Load the user's Emulo profile, mined from their local Claude Code, Codex, and OpenCode session logs, so you work like them instead of a cold start. Use before working on their task.
emoji: 🐦‍⬛
homepage: https://github.com/ohad6k/emulo
metadata:
  openclaw:
    install:
      - kind: uv
        package: emulo
        bins: [emulo]
---

# Emulo profile

Load the user's Emulo working profile so you act like them, not a cold start.

Emulo mines the user's own AI coding sessions (Claude Code, Codex, Cursor,
Copilot) into a `you.md` working profile: their laws, their taste, their voice,
and the failure modes they want you to protect them from.

## Use this before working on their task

Run the profile loader and read what it returns before you plan or edit:

```
emulo --install you.md --target agents
```

Or load it directly through the MCP server:

```
uvx emulo mcp
```

The MCP server exposes one tool, `load_emulo_profile`, which returns the
profile for the domain you are about to work in (`work`, `design`, `write`, or
`video`).

## What you get

The profile is mined from the user's real sessions, not a questionnaire. It
carries:

- **Laws** they never want broken, each with receipts from real sessions
- **Taste** in design and code, including what they reject on sight
- **Voice** for anything written in their name
- **Failure modes** to protect them from

## Privacy

Mining runs locally against session logs already on the machine. The profile is
the user's own file. Nothing is uploaded by this skill.

Previously published as `ditto-profile`. The project was renamed to Emulo in
v0.5.0; see <https://github.com/ohad6k/emulo/releases/tag/v0.5.0>.
