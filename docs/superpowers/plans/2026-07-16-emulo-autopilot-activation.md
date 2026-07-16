# Emulo Autopilot Reviewed Activation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn explicitly approved low-risk candidates into a deterministic supplemental profile overlay, expose the active overlay through Emulo MCP, and provide append-only rollback without modifying the mined base profile.

**Architecture:** Extend the local store with immutable overlay generations and one atomic head pointer. Activation requires the newest append-only decision to be `approve` with policy class `safe` or `review`; artifacts group statements by domain and are content-hashed. The one-file `emulo.py` runtime receives a duplicated, read-only validator so MCP remains usable when installed without the optional Autopilot package.

**Tech Stack:** Python 3.8+ standard library, existing Emulo MCP/profile store, `unittest`.

---

## Boundaries

- No candidate activates from policy output alone.
- No activation without an explicit recorded approval decision.
- Activation only adds candidates to the current active set; retirement/removal requires a later design.
- Candidate statements are single-line plain text. Newlines and control characters are rejected at the contract boundary.
- Overlay files never replace, edit, or migrate the base profile.
- Corrupt head, generation, candidate, decision, or artifact state fails closed.
- Rollback target must be an ancestor of the current head.
- Rollback creates a new generation and head update; it never deletes history or directly repoints to the old generation.
- No CLI, daemon, cloud, billing, or public documentation in this plan.

### Task 1: Harden activatable statements

**Files:**
- Modify: `emulo_autopilot/contracts.py`
- Modify: `tests/test_autopilot_contracts.py`

- [ ] **Step 1: Write a failing test**

Test candidate statements containing `\n`, `\r`, NUL, and other ASCII control characters. Recompute candidate identity before validation and require a `candidate statement` error.

- [ ] **Step 2: Run and verify red state**

Run: `python -m unittest tests.test_autopilot_contracts -v`

Expected: FAIL because multiline statements are currently accepted.

- [ ] **Step 3: Reject non-renderable statements**

Immediately after `_string(value["statement"], ...)`, add:

```python
if any(ord(character) < 32 or ord(character) == 127
       for character in value["statement"]):
    raise ValueError("candidate statement contains a control character")
```

- [ ] **Step 4: Run contract and policy tests**

Run: `python -m unittest tests.test_autopilot_contracts tests.test_autopilot_policy -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add emulo_autopilot/contracts.py tests/test_autopilot_contracts.py
git commit -m "fix: bound activatable Autopilot statements"
```

### Task 2: Immutable generation store and append-only rollback

**Files:**
- Modify: `emulo_autopilot/store.py`
- Modify: `tests/test_autopilot_store.py`

- [ ] **Step 1: Write failing generation tests**

Cover:

- no head returns `None`;
- activation requires existing candidates and newest explicit approvals;
- `reject` decision or policy class `reject` blocks activation;
- candidate IDs and rendered bullets sort deterministically;
- active candidates are retained when a new candidate activates;
- activating an already-active set is idempotent;
- domains render independently;
- manifest and artifact hashes are verified on every read;
- tampered head, manifest, or artifact fails closed;
- failed head write preserves the previous pointer;
- rollback target must be an ancestor;
- rollback creates a new generation whose parent is the former head;
- rollback restores exact target-domain bytes while preserving all generations.

Use one minimal `mock.patch.object(store, "atomic_write_json", ...)` only for the head-write failure. Let generation/artifact writes execute for real and assert the previous head bytes remain exact.

- [ ] **Step 2: Run and verify red state**

Run: `python -m unittest tests.test_autopilot_store -v`

Expected: FAIL because generation methods do not exist.

- [ ] **Step 3: Implement strict head and generation reads**

Add imports for `hashlib`, `shutil`, and generation/head validators and identities. Add these public methods:

```python
    def get_head(self):
        path = self._child("head.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8", errors="strict") as handle:
                return validate_head(json.load(handle))
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Autopilot head is corrupt") from exc

    def get_generation(self, generation_id):
        if not isinstance(generation_id, str) or not re.fullmatch(r"gen_[a-f0-9]{20}", generation_id):
            raise ValueError("generation_id is invalid")
        root = self._child("generations", generation_id)
        self._assert_path_chain(root)
        try:
            with open(os.path.join(root, "generation.json"), "r", encoding="utf-8", errors="strict") as handle:
                generation = validate_generation(json.load(handle))
            if generation["generation_id"] != generation_id:
                raise ValueError
            expected_files = {"generation.json"}
            for domain, metadata in generation["domains"].items():
                expected_files.add(metadata["artifact"])
                path = os.path.join(root, metadata["artifact"])
                with open(path, "rb") as handle:
                    payload = handle.read()
                if hashlib.sha256(payload).hexdigest() != metadata["sha256"]:
                    raise ValueError
                payload.decode("utf-8", errors="strict")
            if set(os.listdir(root)) != expected_files:
                raise ValueError
            return generation
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Autopilot generation is corrupt") from exc

    def read_domain(self, generation_id, domain):
        generation = self.get_generation(generation_id)
        metadata = generation["domains"].get(domain)
        if metadata is None:
            return None
        path = self._child("generations", generation_id, metadata["artifact"])
        with open(path, "r", encoding="utf-8", errors="strict") as handle:
            return handle.read()

    def read_active_domain(self, domain):
        head = self.get_head()
        return None if head is None else self.read_domain(head["generation_id"], domain)
```

Require the generation directory itself and every artifact to be regular non-link/non-reparse paths before reading.

- [ ] **Step 4: Implement deterministic generation writing**

Helpers and rendering:

```python
def render_domain(domain, candidates):
    lines = [
        "# Emulo Autopilot overlay: " + domain,
        "",
        "Evidence-backed personal rules supplementing the active Emulo profile:",
        "",
    ]
    for candidate in sorted(candidates, key=lambda item: item["candidate_id"]):
        lines.append("- " + candidate["statement"])
    return "\n".join(lines).rstrip() + "\n"
```

Implement `_write_generation(candidate_ids, parent_generation_id, operation, created_at)`:

1. Load every candidate and newest decision.
2. Require newest decision `approve` and policy class `safe` or `review`.
3. Sort unique candidate IDs and group candidates by domain.
4. Render UTF-8 artifacts and compute SHA-256 metadata.
5. Build a generation with `generation_identity` and validate it.
6. Create `generations/.staged-<uuid>`, write/fsync artifacts and `generation.json`, then `os.replace` it to the immutable generation directory.
7. If the target already exists, verify it and remove only the staged directory.
8. Atomically write validated `head.json` only after the immutable generation verifies.
9. On failure, remove only the exact staged directory; never remove an immutable generation or previous head.

`activate(candidate_ids, created_at)` acquires `lock("activate")`, loads the current candidate set, unions requested IDs, returns the current generation if unchanged, and otherwise calls `_write_generation(..., operation="activate")`.

`rollback(target_generation_id, created_at)` acquires `lock("rollback")`, walks parent links from current head to prove ancestry, and writes a new generation using the target's candidate IDs with `operation="rollback"` and parent equal to the former head.

- [ ] **Step 5: Run generation and profile-store tests**

Run: `python -m unittest tests.test_autopilot_store tests.test_profile_store -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add emulo_autopilot/store.py tests/test_autopilot_store.py
git commit -m "feat: activate reversible Autopilot overlays"
```

### Task 3: Read-only MCP overlay exposure

**Files:**
- Modify: `emulo.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write failing MCP tests**

Prove:

- absent Autopilot head preserves existing MCP text byte-for-byte;
- a valid work overlay appends after the active base work profile;
- a design overlay never appears in work output;
- rollback changes the appended content to the target generation;
- corrupt head, manifest, extra file, or artifact hash returns an MCP tool error and never partial profile text;
- the one-file `emulo.py` path works without importing `emulo_autopilot`.

- [ ] **Step 2: Run and verify red state**

Run: `python -m unittest tests.test_mcp_server -v`

Expected: new overlay assertions fail.

- [ ] **Step 3: Add a duplicated bounded reader to `emulo.py`**

Add constants for head/generation schemas and implement `load_autopilot_overlay(emulo_home, domain)` without importing the optional package. It must repeat the exact head keys, generation keys, content-bound generation ID, domain metadata, expected-file set, regular-path checks, SHA-256 verification, and strict UTF-8 decoding from Task 2.

Modify `mcp_load_profile_text` only after existing base/legacy composition:

```python
    overlay = load_autopilot_overlay(emulo_home, domain)
    if overlay:
        body += "\n\n" + overlay.rstrip()
    return header + "\n\n" + body
```

Missing `head.json` returns `None`. Any present invalid state raises `ValueError("corrupt Autopilot overlay; inspect local Autopilot status")`, which the existing MCP handler converts to an error result.

- [ ] **Step 4: Run MCP and complete regressions**

Run:

```powershell
python -m unittest tests.test_mcp_server tests.test_autopilot_store tests.test_profile_store -v
python -m unittest discover -s tests -v
```

Expected: full suite passes; existing Windows symlink skips may remain.

- [ ] **Step 5: Commit**

```powershell
git add emulo.py tests/test_mcp_server.py
git commit -m "feat: expose active Autopilot overlay through MCP"
```

## Completion gate

- Full suite passes.
- Base profile bytes and current behavior are unchanged when no Autopilot head exists.
- Only newest explicitly approved candidates activate.
- Activation is additive and idempotent.
- Every read verifies content-bound generation metadata and artifact bytes.
- Rollback is append-only and restores the exact target overlay.
- MCP fails closed on any present corrupt Autopilot state.
- No site, benchmark, video, cloud, billing, or provider dashboard changes.
