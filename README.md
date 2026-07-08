<p align="center"><img src="assets/ditto.png" width="360" alt="ditto"></p>

<h1 align="center">ditto</h1>

<p align="center"><b>your AI agents act like they just met you. ditto fixes that.</b></p>

<p align="center">
you have months of chat logs with claude / codex / cursor sitting on your disk.<br>
it's the most honest record of how you actually think, and you're deleting it.<br>
ditto mines it into a <code>you.md</code> your agents read before every task.
</p>

---

## the receipt

real run. same prompt, same model. one agent cold, one with a `you.md` loaded. i didn't edit their replies.

**prompt:** *"my app works locally but the vercel deploy just shows a white screen. fix it"*

<table>
<tr><th>cold agent</th><th>agent + ditto</th></tr>
<tr valign="top"><td>

> Okay, I've dug into your repo. First, a clarification that matters: your app is a Vite + React SPA, not Next.js, so the env vars are `VITE_*`...
>
> *(five paragraphs: rules out the supabase init, explains lazy-loading and error boundaries, lists two causes with file references)*
>
> ...regardless of what it is, I'd recommend I **add an error boundary** around your routes so a failing chunk shows a real error. Want me to do that now while you pull the console output?

</td><td>

> the two things that white-screen a next+supabase app on vercel but not locally:
>
> 1. missing env vars in vercel. your local `.env` isn't uploaded...
> 2. a client-side crash on first render.
>
> fastest path, do these and tell me what you see: deployed url → F12 → console → paste the red error. vercel → settings → env vars → which names exist.
>
> don't change any code yet. 9 times out of 10 this is the env vars, and rewriting code won't fix a missing key.

</td></tr>
</table>

same model both times. ditto didn't make it smarter. it made it act like **you**: check the provider before the code, keep it short, don't add stuff you didn't ask for (the cold one offered to write a new error boundary into a working app), talk like a builder not a support desk. run ditto on your own logs and it copies *your* rules, not these.

---

## what it does

1. reads your local session logs and keeps **only the words you typed** (strips all the tool output, file dumps, and pasted errors).
2. **redacts secrets + personal info** by default, before anything is written or seen by an agent.
3. splits it into chunks and hands you a prompt to fan a coding agent across them, then merge into one `you.md`.

that `you.md` is a skill/context file. drop it in `.claude/skills/`, your `AGENTS.md`, or cursor rules, and every agent starts already knowing how you work.

## quickstart

```bash
git clone https://github.com/ohad6k/ditto
cd ditto
python ditto.py            # auto-detects Codex + Claude logs. no deps, stdlib only.
```

you get:

```
sessions: 1,656
your messages: 7,678
tokens (approx): 2,950,000
secrets/PII redacted: 41
wrote: ditto-out/you-corpus.txt  +  20 chunks in ditto-out/chunks/
```

then open your coding agent (Claude Code / Codex / Cursor), paste [`MINING_PROMPT.md`](MINING_PROMPT.md), point it at `ditto-out/chunks/`, and let it build your `you.md`. example output: [`examples/you.md`](examples/you.md).

## privacy (read this)

- **100% local.** ditto makes zero network calls. your logs never leave your machine. it's plain python, read the file.
- **redaction is on by default.** API keys, tokens, JWTs, emails, phone numbers, IPs get stripped before your text hits disk or an agent. (`--no-redact` exists; don't use it.)
- the mining step runs in *your* coding agent, on *your* machine. nothing gets uploaded unless you choose to.

## how it works

your logs are ~95% noise (tool output, file contents, diffs). the signal is the small slice of words you actually typed. ditto isolates that, then uses an agent fan-out so no single context has to hold all of it: each agent reads a chunk and pulls how you decide, what you reject, how you talk, where you get stuck. traits that show up across many chunks are the real you. one-offs are noise. that ranking is the whole trick.

## limits (being honest)

- it models how you *work and talk*, not your knowledge. it won't make an agent smarter, it makes it act more like you.
- garbage in, garbage out: if your logs are 3 sessions long, the profile is thin. it shines around months of history.
- it reads Codex (`~/.codex/sessions`) and Claude Code (`~/.claude/projects`) jsonl out of the box. other tools: point `--path` at a folder of jsonl.

## license

MIT. it's yours. if you build something on it, i'd love to see it.

<p align="center"><i>made by <a href="https://github.com/ohad6k">@ohad6k</a> while building in public.</i></p>
