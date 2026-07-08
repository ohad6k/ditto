#!/usr/bin/env python3
"""
ditto — turn your own AI coding sessions into a model of how you think.

It reads your local session logs (Codex / Claude Code / Cursor jsonl), keeps
ONLY the words you typed, redacts secrets + personal info, and writes one
clean corpus + chunks. You then point a coding agent at the chunks with
MINING_PROMPT.md to produce your `you.md`.

100% local. Your logs never leave your machine. No network calls. Stdlib only.

Usage:
    python ditto.py                     # auto-detect Codex + Claude logs
    python ditto.py --source codex      # only ~/.codex/sessions
    python ditto.py --path ./logs       # a folder of jsonl you point at
    python ditto.py --chunks 20         # how many chunks to split into
    python ditto.py --no-redact         # DANGER: skip redaction (not recommended)
"""
import argparse, glob, json, os, re, sys

HOME = os.path.expanduser("~")
SOURCES = {
    "codex":  [os.path.join(HOME, ".codex", "sessions")],
    "claude": [os.path.join(HOME, ".claude", "projects")],
}

# --- redaction: run BEFORE any of your text is written or seen by an agent ---
REDACTIONS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"),                 "[OPENAI_KEY]"),
    (re.compile(r"sk_live_[A-Za-z0-9]{20,}"),            "[STRIPE_KEY]"),
    (re.compile(r"whsec_[A-Za-z0-9]{20,}"),              "[WEBHOOK_SECRET]"),
    (re.compile(r"sbp_[A-Za-z0-9]{20,}"),                "[SUPABASE_TOKEN]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),          "[GITHUB_TOKEN]"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "[JWT]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"),                    "[AWS_KEY]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),       "[SLACK_TOKEN]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
    (re.compile(r"\+?\d[\d\s\-]{8,}\d"),                 "[PHONE]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),         "[IP]"),
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
]

def redact(text):
    for pat, repl in REDACTIONS:
        text = pat.sub(repl, text)
    return text

def is_pasted_log(t):
    """Drop messages that are pasted stack traces / error dumps, not your prose."""
    lines = t.splitlines()
    if len(lines) < 4:
        return False
    hits = sum(1 for l in lines if re.match(r"\s+at ", l) or "Exception" in l
               or "Traceback" in l or re.search(r"\.(java|py|ts|js|kt):\d", l)
               or re.match(r'\s*File "', l))
    return hits / max(len(lines), 1) > 0.25

def user_messages(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"role"' not in line and '"user"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                # Codex: {payload:{type:'message',role:'user',content:[{text}]}}
                # Claude: {type:'user',message:{role:'user',content:'...'|[...]}}
                p = o.get("payload", o)
                msg = p.get("message", p)
                if (p.get("type") == "message" or o.get("type") == "user") and \
                   (p.get("role") == "user" or msg.get("role") == "user"):
                    content = msg.get("content", p.get("content", ""))
                    texts = []
                    if isinstance(content, str):
                        texts = [content]
                    elif isinstance(content, list):
                        texts = [c.get("text", "") for c in content if isinstance(c, dict)]
                    for t in texts:
                        t = (t or "").strip()
                        if not t or t.startswith("<"):        # skip env/system injections
                            continue
                        if is_pasted_log(t):
                            continue
                        ts = (o.get("timestamp", "") or "")[:10]
                        out.append((ts, t))
    except Exception:
        pass
    return out

def main():
    ap = argparse.ArgumentParser(description="mine your AI sessions into a model of you")
    ap.add_argument("--source", choices=["auto", "codex", "claude"], default="auto")
    ap.add_argument("--path", help="a folder of .jsonl session logs to read instead")
    ap.add_argument("--out", default="ditto-out")
    ap.add_argument("--chunks", type=int, default=20)
    ap.add_argument("--no-redact", action="store_true", help="skip redaction (NOT recommended)")
    args = ap.parse_args()

    roots = []
    if args.path:
        roots = [args.path]
    elif args.source == "auto":
        roots = SOURCES["codex"] + SOURCES["claude"]
    else:
        roots = SOURCES[args.source]

    files = []
    for r in roots:
        files += glob.glob(os.path.join(r, "**", "*.jsonl"), recursive=True)
    files = sorted(set(files))
    if not files:
        print("no session logs found. try --path <folder> or --source codex/claude.")
        print("looked in:", ", ".join(roots))
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    chunks_dir = os.path.join(args.out, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)

    sessions = msgs = chars = redactions = 0
    blocks = []
    for f in files:
        ums = user_messages(f)
        if not ums:
            continue
        sessions += 1
        buf = [f"\n===== {os.path.basename(f)} ====="]
        for ts, t in ums:
            if not args.no_redact:
                before = t
                t = redact(t)
                if t != before:
                    redactions += 1
            buf.append(f"[{ts}]\n{t}")
            msgs += 1
            chars += len(t)
        blocks.append("\n".join(buf))

    corpus = "\n".join(blocks)
    with open(os.path.join(args.out, "you-corpus.txt"), "w", encoding="utf-8") as w:
        w.write(corpus)

    # split on session boundaries into ~N chunks
    n = max(1, args.chunks)
    target = max(1, len(corpus) // n)
    cur, size, idx = [], 0, 1
    for b in blocks:
        cur.append(b); size += len(b)
        if size >= target:
            with open(os.path.join(chunks_dir, f"chunk-{idx:02d}.txt"), "w", encoding="utf-8") as w:
                w.write("\n".join(cur))
            idx += 1; cur, size = [], 0
    if cur:
        with open(os.path.join(chunks_dir, f"chunk-{idx:02d}.txt"), "w", encoding="utf-8") as w:
            w.write("\n".join(cur))

    print(f"sessions: {sessions}")
    print(f"your messages: {msgs}")
    print(f"tokens (approx): {chars // 4:,}")
    print(f"secrets/PII redacted: {redactions}" + ("  (redaction OFF)" if args.no_redact else ""))
    print(f"wrote: {args.out}/you-corpus.txt  +  {idx} chunks in {args.out}/chunks/")
    print(f"\nnext: open your coding agent, paste MINING_PROMPT.md, point it at {args.out}/chunks/, merge into you.md")

if __name__ == "__main__":
    main()
