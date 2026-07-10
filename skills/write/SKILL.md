---
name: write
description: Use for marketing, social, replies, product copy, launch copy, and writing in the user's voice when their Ditto writing profile should guide the task. Do not use for unrelated execution or UI/UX design alone.
---

# Ditto write

1. Locate `ditto.py` two directories above this skill; fall back to `./ditto.py` only for a direct repo checkout.
2. Store the resolved absolute runtime path as `DITTO_PY`, then run `python "$DITTO_PY" plugin profile-path --domain write`.
3. If it exits nonzero, give its exact recovery or targeted-deepen instruction and stop loading personal context.
4. Read every returned path completely. The first is the core working profile; the second is the writing profile. Apply both.
5. Never imitate a generic voice when the writing domain is inactive.
