# ditto — mining prompt

After running `ditto.py`, paste this into your coding agent (Claude Code / Codex / Cursor). It works two ways:

- **Fan-out (best):** tell your agent to spawn one sub-agent per file in `ditto-out/chunks/`, each running the prompt below on its chunk, then merge all reports with the reducer at the bottom.
- **Simple:** run the prompt below once per chunk yourself, paste the outputs together, then run the reducer.

---

## per-chunk prompt

```
You are mining a chunk of ONE person's real messages to AI coding assistants,
across months and several projects. The file contains ONLY their own words —
mostly short directives, occasionally long specs — each prefixed with a [date].

Read the ENTIRE file at: <path-to-chunk>

Extract a dense, SPECIFIC profile. Ban generic filler ("they want working code",
"they value quality"). Every bullet must be something a stranger could NOT have
guessed — grounded in what they actually wrote. Cite dates. Prefer verbatim quotes.

Return markdown with these EXACT headers:

## DECISIONS & PIVOTS
Concrete choices / direction-changes and (if visible) why.

## VOICE & LANGUAGE
How they actually write: recurring phrases, tics, spelling patterns, tone, how
they give orders, how they show frustration or approval. 6-10 verbatim short quotes.

## STUCK-POINTS & FRICTION
What repeatedly trips them up. Recurring bugs, tools that fail them, what they
ask for over and over, what makes them angry.

## REJECTIONS & DISLIKES
What they push back on, correct, or hate. What they say NOT to do.

## WORK-STYLE & OPERATING RHYTHM
Pace, when they spec vs one-line, how they delegate, verification habits.

## GOALS & DRIVES
What they're reaching for. Quote the raw ambition where it appears.

## RULES THEY STATE
Any rule/law they repeat unprompted ("only done when X", "never Y").

## SHARPEST QUOTES
The 5-8 lines that most capture who they are.

Be information-dense. Your whole response IS the data. No preamble.
```

---

## reducer prompt (run once over all the chunk reports)

```
Below are N independent profiles of the same person, each mined from a different
slice of their history. Merge them into ONE model.

Rank every trait by how many of the N reports independently surfaced it. A trait
found in many reports is the real them; a trait in one report is noise — cut it or
mark it low-confidence.

Output a tight `you.md` an AI agent reads before any task. Start the file with
this EXACT frontmatter so it installs as a skill unchanged (do not skip it):

---
name: you
description: <one line: this person's working profile — laws, taste, voice — so the agent acts like them, not a stranger>
---

Then the body, with sections:
- Who they are (one paragraph)
- Their laws (rules they state, ranked by frequency)
- How to talk to them
- How they work / build
- Their taste (produce this / reject that)
- Their voice (for writing copy as them)
- Their failure modes (protect them from these)
- The one throughline

Keep it lean — it loads on every task. Put deep evidence/quotes in a separate
appendix file, not in you.md.
```
