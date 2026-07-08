---
name: ditto
description: Mine your own AI coding-session history into a "you.md" — a model of how you decide, talk, work, and get stuck — that your agents read before every task so they act like you instead of a stranger. Use when someone wants to clone their working style, build a personal agent profile, generate a you.md / AGENTS.md from their real history, or "make my agent act like me." Runs 100% local; redacts secrets first.
---

# ditto

Turn the user's own AI session logs into a `you.md` they can drop into `.claude/skills/`, `AGENTS.md`, or cursor rules. Runs locally, redacts secrets by default. This skill orchestrates the whole flow so the user never touches python or a manual step.

## Steps

1. **Extract (deterministic, safe).** Run the bundled extractor. It reads the user's session logs, keeps only their own words, and redacts API keys / tokens / emails / phone numbers BEFORE anything is written. Never skip redaction.
   ```
   python <skill-dir>/../ditto.py --chunks 20 --out ditto-out
   ```
   If no logs are found, ask where their logs live and pass `--path <folder>`. Report the counts it prints (sessions / messages / tokens / redactions).

2. **Mine (fan-out).** Spawn one sub-agent per file in `ditto-out/chunks/`, each running the per-chunk prompt from `MINING_PROMPT.md` on its chunk. Run them in parallel. Each returns a structured profile of one slice.
   - If the environment can't fan out sub-agents, process chunks sequentially instead — same prompt, one at a time.

3. **Reduce.** Merge all the chunk reports with the reducer prompt in `MINING_PROMPT.md`. Rank every trait by how many chunks independently surfaced it — high-frequency traits are the real person, one-offs are noise. Output a lean `you.md` (deep quotes go in a separate `you-appendix.md`, not in `you.md`).

4. **Install + prove.** The `you.md` already starts with `name:` / `description:` frontmatter, so it's skill-ready. Place it where the user's agent actually reads it, per their tool, then verify it registered:
   - **Claude Code** → save as `.claude/skills/you/SKILL.md`. Confirm it shows in the skill list (invoke `/you`). For it to load in every project, put it in the user-level `~/.claude/skills/you/SKILL.md`.
   - **Codex** → append the body (everything below the frontmatter) to `AGENTS.md` at the repo root. Codex reads it automatically, no frontmatter needed.
   - **Cursor** → save as `.cursor/rules/you.mdc`, with frontmatter `description: act like me` and `alwaysApply: true`, then the body.
   - **Gemini CLI** → append the body to `GEMINI.md`.
   Then prove it: run one real task once without the file and once with it loaded, so the user sees the agent act more like them. Do not claim it's installed until you've confirmed the agent actually picks it up.

## Rules
- **Local only.** No network calls. The user's logs never leave their machine. Say so.
- **Redaction is not optional.** If the user asks for `--no-redact`, warn them their secrets will appear in the corpus and any shared output.
- **Don't invent traits.** Every line in `you.md` must trace to something they actually wrote. Cut generic filler.
- Keep `you.md` lean — it loads on every task.
