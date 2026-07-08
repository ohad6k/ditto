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

4. **Install + prove.** Offer to place `you.md` where their agent will read it (`.claude/skills/you/SKILL.md`, `AGENTS.md`, or `.cursor/rules`). Then show a quick receipt: answer one real task once cold and once with `you.md` loaded, so they see it behaves more like them.

## Rules
- **Local only.** No network calls. The user's logs never leave their machine. Say so.
- **Redaction is not optional.** If the user asks for `--no-redact`, warn them their secrets will appear in the corpus and any shared output.
- **Don't invent traits.** Every line in `you.md` must trace to something they actually wrote. Cut generic filler.
- Keep `you.md` lean — it loads on every task.
