# security model

ditto reads private AI session logs, so the security model has to be easy to audit.

## what it reads

By default, `ditto.py` looks for local JSONL logs in:

- `~/.codex/sessions`
- `~/.claude/projects`

You can point it at another folder with:

```bash
python ditto.py --path ./some-jsonl-folder
```

Preview what ditto would do without writing output files:

```bash
python ditto.py --dry-run
```

## what it writes

ditto writes only to the output folder you choose. The default is:

```text
ditto-out/
```

It creates:

- `ditto-out/you-corpus.txt`
- `ditto-out/chunks/chunk-01.txt`
- more chunk files depending on `--chunks`

## network

`ditto.py` makes no network calls. It uses only Python stdlib modules.

You can verify that in the source:

- no `requests`
- no `urllib`
- no `httpx`
- no SDK client
- no subprocess upload step

The later mining step happens in your own coding agent, on your own machine. Nothing leaves your machine unless you choose to paste/upload it somewhere.

## redaction

Redaction runs before your text is written to disk.

Current redaction patterns cover:

- OpenAI keys
- Stripe live keys
- Stripe webhook secrets
- Supabase tokens
- GitHub tokens
- JWTs
- AWS access keys
- Slack tokens
- emails
- phone numbers
- IP addresses
- common `api_key`, `secret`, `token`, `password`, `passwd` assignments

The patterns live in `REDACTIONS` inside [`ditto.py`](ditto.py).

## important limits

Redaction is best-effort. You should still inspect generated files before sharing anything publicly.

Do not use `--no-redact` unless you know exactly what is in your logs.

Do not commit `ditto-out/`, `you-corpus.txt`, chunks, or your real `you.md`. The `.gitignore` blocks those by default.

## safe sharing

If you want to share results, share a short summary of what ditto found, not your full profile.

Good:

```text
it noticed i reject "done" unless there is live proof
```

Bad:

```text
here is my whole you.md with project names and private workflows
```
