# Ditto Benchmark/Proof Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a disabled-by-default, privacy-safe Ditto Proof v1 harness that freezes 24 paired comparisons, validates 48 isolated executions, and produces a sanitized evidence package without changing normal Ditto behavior.

**Architecture:** Add a standalone stdlib-only `proof` package beside `ditto.py`. It seals deterministic fixtures, freezes complete-system manifests, creates fresh per-cell homes and workspaces, records append-only evidence, validates objective and independent-review outcomes, and emits a static sanitized package only after every gate passes. Private profiles, provider commands, run artifacts, reviewer identity, and unreleased primary/held-out fixtures stay under an explicit run root outside Git.

**Tech Stack:** Python 3.8+ stdlib, `unittest`, JSON/JSONL, SHA-256, subprocess argv execution with `shell=False`, static HTML/Markdown.

---

## Scope and file map

This is one subsystem: the Ditto Proof v1 harness and its publication generator. Proof clips, provider purchasing, reviewer recruitment, benchmark execution, and public shipping remain later gated operations.

- Create `proof/__init__.py`: frozen schema/benchmark constants.
- Create `proof/canonical.py`: canonical JSON, hashing, safe paths, atomic and write-once primitives.
- Create `proof/schema.py`: exact-key validation for manifests, cells, reviews, and publication records.
- Create `proof/fixtures.py`: seal, hash, verify, and deterministically reset fixtures.
- Create `proof/manifest.py`: system freeze, 24-pair matrix construction, immutable tuple validation, opaque review IDs, and randomized order.
- Create `proof/store.py`: append-only attempts, evaluations, invalidations, superseding records, and retry selection.
- Create `proof/runner.py`: clean-home audit, isolated workspace preparation, explicit approval gate, and host execution.
- Create `proof/evaluate.py`: objective checks, hard-failure capture, independent-review validation, and Wilson intervals.
- Create `proof/privacy.py`: canary detection, path/profile/secret scanning, and fail-closed sanitization.
- Create `proof/publish.py`: aggregate recalculation and static evidence package generation.
- Create `proof/cli.py`: read-only commands by default; execution requires an exact manifest-hash approval.
- Create `proof/schemas/*.json`: public machine-readable contracts matching `proof/schema.py`.
- Create `proof/fixtures/pilot/*`: three separate non-scored schema fixtures.
- Create `tests/test_proof_*.py`: focused unit and integration coverage.
- Create `docs/proof/README.md`: operator runbook, consent flow, limitations, and ship gates.
- Create `docs/proof/example-publication/`: sanitized generated example only, never real private artifacts.
- Modify `.gitignore`: exclude `.ditto-proof-private/`, `proof-private/`, and local run roots.
- Modify `README.md`: add one non-promotional link to the proof methodology after implementation is verified; do not add outcome claims.

Do not modify `ditto.py`, `MINING_PROMPT.md`, plugin manifests, skills, profile schemas, mining defaults, Antigravity files, or the main `D:\ditto` worktree.

## Frozen contracts

- Benchmark name: `Ditto Proof v1`.
- Benchmark schema: `ditto-proof/1`.
- Frozen Ditto ref: `v0.3.7`.
- Frozen Ditto commit: `5f4008b0c0df40dcadb92c8fd1ba4dcf3aee40d0`.
- Matrix: 2 systems x 3 families x 2 variants x 2 trials = 24 pairs and 48 cells.
- Families: `work`, `design`, `write`.
- Variants: `primary`, `held-out`.
- Conditions: `cold`, `ditto`.
- Host-native persistent personalization: `absent` in every cell.
- Private run root must be absolute, outside the repository, and explicitly supplied.
- System labels, host versions, provider argv, quotas, and expected cost are captured from live provider interfaces during preflight; they are evidence inputs, not hard-coded guesses.
- Primary and held-out v1 fixture content is sealed under the private run root before the pilot. Only hashes and task IDs enter the manifest until the final approved publication package.
- The six-execution pilot uses committed `pilot-*` fixtures and can never contribute to v1 outcomes.
- No provider command runs unless the operator supplies both `--execute` and `--approval <manifest_sha256>`.
- No public package is written unless all validation, privacy, completeness, and explicit ship-approval inputs pass.

### Task 1: Canonical evidence primitives

**Files:**
- Create: `proof/__init__.py`
- Create: `proof/canonical.py`
- Test: `tests/test_proof_canonical.py`

- [ ] **Step 1: Write failing canonicalization and write-once tests**

```python
import json
import tempfile
import unittest
from pathlib import Path

from proof.canonical import canonical_bytes, safe_child, sha256_bytes, write_once_json


class CanonicalEvidenceTest(unittest.TestCase):
    def test_canonical_json_is_order_independent_and_utf8_exact(self):
        left = canonical_bytes({"hebrew": "שלום", "count": 2})
        right = canonical_bytes({"count": 2, "hebrew": "שלום"})
        self.assertEqual(left, right)
        self.assertEqual(b'{"count":2,"hebrew":"\\u05e9\\u05dc\\u05d5\\u05dd"}', left)

    def test_safe_child_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "outside root"):
                safe_child(Path(tmp), "..", "escape")

    def test_write_once_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            digest = write_once_json(path, {"state": "first"})
            self.assertEqual(sha256_bytes(path.read_bytes()), digest)
            with self.assertRaises(FileExistsError):
                write_once_json(path, {"state": "second"})
            self.assertEqual({"state": "first"}, json.loads(path.read_text("utf-8")))
```

- [ ] **Step 2: Run the tests and verify the import fails**

Run: `python -m unittest tests.test_proof_canonical -v`

Expected: `ERROR` with `ModuleNotFoundError: No module named 'proof'`.

- [ ] **Step 3: Implement the frozen constants and canonical primitives**

```python
# proof/__init__.py
BENCHMARK_NAME = "Ditto Proof v1"
BENCHMARK_SCHEMA = "ditto-proof/1"
DITTO_REF = "v0.3.7"
DITTO_COMMIT = "5f4008b0c0df40dcadb92c8fd1ba4dcf3aee40d0"
FAMILIES = ("work", "design", "write")
VARIANTS = ("primary", "held-out")
CONDITIONS = ("cold", "ditto")
TRIALS = (1, 2)
```

```python
# proof/canonical.py
import hashlib
import json
import os
from pathlib import Path


def canonical_bytes(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_child(root, *parts):
    root = Path(root).resolve()
    child = root.joinpath(*parts).resolve()
    try:
        child.relative_to(root)
    except ValueError as exc:
        raise ValueError("path is outside root") from exc
    return child


def write_once_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value) + b"\n"
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return sha256_bytes(payload)
```

- [ ] **Step 4: Run the focused tests**

Run: `python -m unittest tests.test_proof_canonical -v`

Expected: `Ran 3 tests` and `OK`.

- [ ] **Step 5: Commit the foundation**

```bash
git add proof/__init__.py proof/canonical.py tests/test_proof_canonical.py
git commit -m "test: add canonical proof evidence primitives"
```

### Task 2: Exact schemas and incompatible-version rejection

**Files:**
- Create: `proof/schema.py`
- Create: `proof/schemas/benchmark-manifest-v1.json`
- Create: `proof/schemas/cell-record-v1.json`
- Create: `proof/schemas/review-record-v1.json`
- Create: `proof/schemas/publication-v1.json`
- Test: `tests/test_proof_schema.py`

- [ ] **Step 1: Write failing tests for required fields, exact keys, and versions**

```python
import unittest

from proof.schema import validate_cell, validate_manifest


def minimal_manifest():
    return {
        "schema": "ditto-proof/1",
        "benchmark": "Ditto Proof v1",
        "benchmark_version": "1.0.0",
        "ditto_ref": "v0.3.7",
        "ditto_commit": "5f4008b0c0df40dcadb92c8fd1ba4dcf3aee40d0",
        "profile_manifest_sha256": "a" * 64,
        "private_rubric_sha256": "b" * 64,
        "public_rubric_sha256": "c" * 64,
        "uncertainty_policy": "small-n, directional only; Wilson 95%; no significance claims",
        "systems": [],
        "pairs": [],
        "created_at": "2026-07-15T00:00:00Z",
    }


class ProofSchemaTest(unittest.TestCase):
    def test_manifest_rejects_unknown_version(self):
        value = minimal_manifest()
        value["schema"] = "ditto-proof/2"
        with self.assertRaisesRegex(ValueError, "unsupported schema"):
            validate_manifest(value)

    def test_manifest_rejects_unknown_key(self):
        value = minimal_manifest()
        value["surprise"] = True
        with self.assertRaisesRegex(ValueError, "unexpected keys: surprise"):
            validate_manifest(value)

    def test_cell_requires_clean_host_state(self):
        with self.assertRaisesRegex(ValueError, "persistent context"):
            validate_cell({"schema": "ditto-proof-cell/1", "host_persistent_context": "present"})
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m unittest tests.test_proof_schema -v`

Expected: `ERROR` because `proof.schema` does not exist.

- [ ] **Step 3: Implement strict structural validation**

```python
# proof/schema.py
from proof import BENCHMARK_NAME, BENCHMARK_SCHEMA, DITTO_COMMIT, DITTO_REF

SHA256_LENGTH = 64
MANIFEST_KEYS = {
    "schema", "benchmark", "benchmark_version", "ditto_ref", "ditto_commit",
    "profile_manifest_sha256", "private_rubric_sha256", "public_rubric_sha256",
    "uncertainty_policy", "systems", "pairs", "created_at",
}


def require_exact_keys(value, required, label):
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing:
        raise ValueError(f"{label} missing keys: {', '.join(missing)}")
    if extra:
        raise ValueError(f"{label} unexpected keys: {', '.join(extra)}")


def require_sha256(value, label):
    if not isinstance(value, str) or len(value) != SHA256_LENGTH:
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be lowercase hex")


def validate_manifest(value):
    require_exact_keys(value, MANIFEST_KEYS, "manifest")
    if value["schema"] != BENCHMARK_SCHEMA:
        raise ValueError("unsupported schema")
    if value["benchmark"] != BENCHMARK_NAME:
        raise ValueError("wrong benchmark name")
    if value["ditto_ref"] != DITTO_REF or value["ditto_commit"] != DITTO_COMMIT:
        raise ValueError("mixed Ditto version")
    for key in ("profile_manifest_sha256", "private_rubric_sha256", "public_rubric_sha256"):
        require_sha256(value[key], key)
    if value["uncertainty_policy"] != "small-n, directional only; Wilson 95%; no significance claims":
        raise ValueError("uncertainty policy changed")
    return value


def validate_cell(value):
    if value.get("schema") != "ditto-proof-cell/1":
        raise ValueError("unsupported cell schema")
    if value.get("host_persistent_context") != "absent":
        raise ValueError("host persistent context must be absent")
    return value
```

- [ ] **Step 4: Add JSON schemas that mirror every Python-required key**

Use Draft 2020-12, set `additionalProperties` to `false`, enumerate frozen values, and require every field accepted by the Python validators. The manifest schema must constrain `systems` to exactly 2 items and `pairs` to exactly 24 items. The cell schema must require artifact hashes, instruction hashes, budgets, attempts, objective results, hard failures, redaction state, and publication state. The review schema must require consent reference, eligibility attestation, blinding confirmation, verdict, and invalidation reason. The publication schema must require denominators, exclusions, invalidations, limitations, and record hashes.

- [ ] **Step 5: Add schema-file parity tests and run them**

```python
def test_json_manifest_schema_matches_python_required_keys(self):
    schema = json.loads((ROOT / "proof/schemas/benchmark-manifest-v1.json").read_text("utf-8"))
    self.assertFalse(schema["additionalProperties"])
    self.assertEqual(sorted(MANIFEST_KEYS), sorted(schema["required"]))
    self.assertEqual(2, schema["properties"]["systems"]["minItems"])
    self.assertEqual(24, schema["properties"]["pairs"]["minItems"])
```

Run: `python -m unittest tests.test_proof_schema -v`

Expected: all schema tests pass.

- [ ] **Step 6: Commit schema contracts**

```bash
git add proof/schema.py proof/schemas tests/test_proof_schema.py
git commit -m "feat: freeze Ditto Proof v1 schemas"
```

### Task 3: Private fixture sealing and deterministic resets

**Files:**
- Create: `proof/fixtures.py`
- Test: `tests/test_proof_fixtures.py`

- [ ] **Step 1: Write failing tests for sealing, reset, and held-out privacy**

```python
import tempfile
import unittest
from pathlib import Path

from proof.fixtures import reset_fixture, seal_fixture, verify_fixture


class FixtureTest(unittest.TestCase):
    def test_reset_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "brief.txt").write_text("שלום\n", encoding="utf-8")
            sealed = seal_fixture(source, root / "private", "work-primary")
            first = reset_fixture(sealed, root / "cell-a")
            second = reset_fixture(sealed, root / "cell-b")
            self.assertEqual(verify_fixture(first), verify_fixture(second))

    def test_seal_rejects_repository_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "outside repository"):
                seal_fixture(Path(tmp), ROOT, "write-held-out")

    def test_reset_refuses_nonempty_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "used"
            destination.mkdir()
            (destination / "old.txt").write_text("contamination", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "workspace must not exist"):
                reset_fixture(Path(tmp) / "sealed", destination)
```

- [ ] **Step 2: Run the tests and observe failure**

Run: `python -m unittest tests.test_proof_fixtures -v`

Expected: import failure for `proof.fixtures`.

- [ ] **Step 3: Implement sorted tree hashing and immutable fixture locks**

```python
# proof/fixtures.py
import shutil
import subprocess
from pathlib import Path

from proof.canonical import canonical_bytes, sha256_bytes, sha256_file, write_once_json


def tree_manifest(root):
    root = Path(root).resolve()
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and ".git" not in item.parts):
        relative = path.relative_to(root).as_posix()
        rows.append({"path": relative, "sha256": sha256_file(path), "size": path.stat().st_size})
    return rows


def tree_hash(root):
    return sha256_bytes(canonical_bytes(tree_manifest(root)))


def seal_fixture(source, private_root, task_id, repository_root=None):
    source = Path(source).resolve()
    private_root = Path(private_root).resolve()
    repository_root = Path(repository_root or Path(__file__).resolve().parents[1]).resolve()
    try:
        private_root.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise ValueError("private fixture root must be outside repository")
    status = subprocess.check_output(
        ["git", "-C", str(source), "status", "--porcelain"], text=True
    )
    if status.strip():
        raise ValueError("fixture source must be a clean Git commit")
    fixture_commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    destination = private_root / "sealed-fixtures" / task_id
    if destination.exists():
        raise FileExistsError("sealed fixture already exists")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git"))
    lock = {"schema": "ditto-proof-fixture/1", "task_id": task_id,
            "fixture_commit": fixture_commit, "files": tree_manifest(destination),
            "fixture_sha256": tree_hash(destination)}
    write_once_json(private_root / "fixture-locks" / f"{task_id}.json", lock)
    return destination


def verify_fixture(path):
    return tree_hash(path)


def reset_fixture(sealed, destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("workspace must not exist")
    shutil.copytree(sealed, destination)
    return destination
```

- [ ] **Step 4: Add tests that reject symlinks, path traversal, changed bytes, and missing files**

The implementation must reject symlinks in source fixtures, require normalized relative paths, require a clean Git commit, compare the reset hash with the sealed lock, and never delete or reuse an existing cell workspace.

Run: `python -m unittest tests.test_proof_fixtures -v`

Expected: all fixture tests pass on Windows and preserve UTF-8/Hebrew bytes.

- [ ] **Step 5: Commit fixture isolation**

```bash
git add proof/fixtures.py tests/test_proof_fixtures.py
git commit -m "feat: seal and reset private proof fixtures"
```

### Task 4: Freeze systems and build the exact 24-pair matrix

**Files:**
- Create: `proof/manifest.py`
- Test: `tests/test_proof_manifest.py`

- [ ] **Step 1: Write failing matrix and identity tests**

```python
import unittest

from proof.manifest import build_pairs, build_system_freeze


class ManifestTest(unittest.TestCase):
    def test_builds_24_pairs_and_48_unique_cells(self):
        systems = [
            build_system_freeze("codex", "Visible Codex Label", "model-id-a", "0.1", ["codex", "exec"], "a" * 64),
            build_system_freeze("claude", "Visible Claude Label", "model-id-b", "0.2", ["claude", "-p"], "b" * 64),
        ]
        pairs = build_pairs(systems, fixture_hashes=FIXTURE_HASHES, seed="c" * 64)
        self.assertEqual(24, len(pairs))
        self.assertEqual(48, len({cell["cell_id"] for pair in pairs for cell in pair["cells"]}))
        self.assertEqual({"cold", "ditto"}, {cell["condition"] for cell in pairs[0]["cells"]})

    def test_mini_or_preview_label_is_ineligible(self):
        with self.assertRaisesRegex(ValueError, "ineligible system label"):
            build_system_freeze("codex", "5.4 Mini", "model", "1", ["codex"], "d" * 64)
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `python -m unittest tests.test_proof_manifest -v`

Expected: import failure for `proof.manifest`.

- [ ] **Step 3: Implement system capture, deterministic IDs, and order randomization**

```python
# proof/manifest.py
import hashlib
import random

from proof import CONDITIONS, FAMILIES, TRIALS, VARIANTS
from proof.canonical import canonical_bytes


def stable_id(prefix, value):
    return f"{prefix}-{hashlib.sha256(canonical_bytes(value)).hexdigest()[:16]}"


def build_system_freeze(host, menu_label, model_id, host_version, run_argv, screenshot_sha256):
    lowered = menu_label.lower()
    if "mini" in lowered or "preview" in lowered or "fast" in lowered:
        raise ValueError("ineligible system label")
    if host not in ("codex", "claude"):
        raise ValueError("host must be codex or claude")
    if not isinstance(run_argv, list) or not run_argv or not all(isinstance(x, str) for x in run_argv):
        raise ValueError("run_argv must be a nonempty argv list")
    return {"host": host, "menu_label": menu_label, "model_id": model_id or None,
            "host_version": host_version, "run_argv": run_argv,
            "selection_screenshot_sha256": screenshot_sha256}


def build_pairs(systems, fixture_hashes, seed):
    if len(systems) != 2 or {item["host"] for item in systems} != {"codex", "claude"}:
        raise ValueError("v1 requires one Codex-host and one Claude-host system")
    pairs = []
    for system in systems:
        for family in FAMILIES:
            for variant in VARIANTS:
                task_id = f"{family}-{variant}"
                for trial in TRIALS:
                    base = {"system": system["menu_label"], "host": system["host"],
                            "task_id": task_id, "family": family, "variant": variant,
                            "trial": trial, "fixture_sha256": fixture_hashes[task_id]}
                    pair_id = stable_id("pair", base)
                    order = list(CONDITIONS)
                    random.Random(f"{seed}:{pair_id}").shuffle(order)
                    cells = [{**base, "pair_id": pair_id, "condition": condition,
                              "order": index + 1,
                              "cell_id": stable_id("cell", {**base, "condition": condition}),
                              "review_id": stable_id("review", {"pair_id": pair_id, "condition": condition, "seed": seed})}
                             for index, condition in enumerate(order)]
                    pairs.append({"pair_id": pair_id, "cells": cells})
    return pairs
```

- [ ] **Step 4: Add invariant tests**

Cover changed seeds, unique opaque IDs, no condition text inside review IDs, exactly two trials, exact fixture commits and hashes, unavailable-system refusal, no substitution field, captured menu labels/model IDs/host versions, budgets, tool/permission policy, instruction hashes, clean-home state, and the frozen uncertainty policy.

Run: `python -m unittest tests.test_proof_manifest -v`

Expected: all manifest tests pass and the pair count is exactly 24.

- [ ] **Step 5: Commit matrix construction**

```bash
git add proof/manifest.py tests/test_proof_manifest.py
git commit -m "feat: freeze the 24-pair proof matrix"
```

### Task 5: Append-only attempts, retries, and invalidations

**Files:**
- Create: `proof/store.py`
- Test: `tests/test_proof_store.py`

- [ ] **Step 1: Write failing lifecycle tests**

```python
class EvidenceStoreTest(unittest.TestCase):
    def test_model_failure_is_scored_without_retry(self):
        store = EvidenceStore(self.root)
        store.record_attempt("cell-a", attempt("model_error", meaningful=True))
        with self.assertRaisesRegex(ValueError, "result, not retryable"):
            store.authorize_retry("cell-a")

    def test_provider_failure_allows_one_retained_retry(self):
        store = EvidenceStore(self.root)
        store.record_attempt("cell-a", attempt("provider_error", meaningful=False))
        store.authorize_retry("cell-a")
        store.record_attempt("cell-a", attempt("ok", meaningful=True))
        self.assertEqual(2, len(store.attempts("cell-a")))
        with self.assertRaisesRegex(ValueError, "one retry"):
            store.authorize_retry("cell-a")

    def test_correction_creates_superseding_record(self):
        first = self.store.record_evaluation("cell-a", evaluation())
        second = self.store.supersede_evaluation("cell-a", first, "clerical correction", evaluation())
        self.assertNotEqual(first, second)
        self.assertTrue(self.store.load(second)["supersedes_sha256"])
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `python -m unittest tests.test_proof_store -v`

Expected: import failure for `proof.store`.

- [ ] **Step 3: Implement one-file-per-event write-once storage**

```python
# proof/store.py
import json
from pathlib import Path

from proof.canonical import safe_child, write_once_json

RETRYABLE = {"provider_error", "host_error_before_output"}


class EvidenceStore:
    def __init__(self, run_root):
        self.root = Path(run_root).resolve()

    def _events(self, cell_id, kind):
        folder = safe_child(self.root, "cells", cell_id, kind)
        return sorted(folder.glob("*.json")) if folder.exists() else []

    def _append(self, cell_id, kind, value):
        index = len(self._events(cell_id, kind)) + 1
        path = safe_child(self.root, "cells", cell_id, kind, f"{index:04d}.json")
        digest = write_once_json(path, value)
        return {"path": str(path), "sha256": digest}

    def attempts(self, cell_id):
        return [json.loads(path.read_text("utf-8")) for path in self._events(cell_id, "attempts")]

    def record_attempt(self, cell_id, value):
        if len(self.attempts(cell_id)) >= 2:
            raise ValueError("cell already has the maximum two attempts")
        return self._append(cell_id, "attempts", value)

    def authorize_retry(self, cell_id):
        attempts = self.attempts(cell_id)
        if len(attempts) != 1:
            raise ValueError("one retry requires exactly one prior attempt")
        prior = attempts[0]
        if prior["meaningful_output"] or prior["exit_status"] not in RETRYABLE:
            raise ValueError("model behavior is a result, not retryable")
        return True

    def record_evaluation(self, cell_id, value):
        return self._append(cell_id, "evaluations", value)["sha256"]

    def supersede_evaluation(self, cell_id, prior_sha256, reason, value):
        corrected = dict(value, supersedes_sha256=prior_sha256, supersession_reason=reason)
        return self.record_evaluation(cell_id, corrected)
```

- [ ] **Step 4: Add contamination and version-mixing invalidation tests**

Reject mismatched Ditto ref/profile/system/fixture/budget/instruction hashes, reused workspace IDs, manually reconstructed transcripts, and changed tool policy. A leaked condition label invalidates only the blind verdict; cross-cell filesystem or memory reuse invalidates the pair. Every invalidation and exclusion remains in the store.

Run: `python -m unittest tests.test_proof_store -v`

Expected: all lifecycle tests pass.

- [ ] **Step 5: Commit evidence lifecycle rules**

```bash
git add proof/store.py tests/test_proof_store.py
git commit -m "feat: add append-only proof evidence lifecycle"
```

### Task 6: Clean-host workspace and explicit execution gate

**Files:**
- Create: `proof/runner.py`
- Create: `proof/cli.py`
- Test: `tests/test_proof_runner.py`

- [ ] **Step 1: Write failing default-disabled and isolation tests**

```python
class RunnerTest(unittest.TestCase):
    def test_execute_requires_flag_and_exact_manifest_hash(self):
        with self.assertRaisesRegex(PermissionError, "explicit approval"):
            execute_cell(self.manifest, self.cell, self.root, execute=False, approval="")
        with self.assertRaisesRegex(PermissionError, "manifest hash"):
            execute_cell(self.manifest, self.cell, self.root, execute=True, approval="0" * 64)

    def test_pair_cells_get_different_workspaces_and_homes(self):
        cold = prepare_cell(self.manifest, self.cold, self.root)
        ditto = prepare_cell(self.manifest, self.ditto, self.root)
        self.assertNotEqual(cold.workspace, ditto.workspace)
        self.assertNotEqual(cold.home, ditto.home)
        self.assertEqual(cold.fixture_sha256, ditto.fixture_sha256)

    def test_clean_home_rejects_native_personalization(self):
        home = self.root / "home"
        home.mkdir()
        (home / "AGENTS.md").write_text("private rules", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "persistent context"):
            audit_clean_home(home)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_proof_runner -v`

Expected: import failure for `proof.runner`.

- [ ] **Step 3: Implement fresh cell preparation and home auditing**

```python
# proof/runner.py
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from proof.canonical import canonical_bytes, safe_child, sha256_bytes
from proof.fixtures import reset_fixture, tree_hash

FORBIDDEN_CONTEXT = ("AGENTS.md", "CLAUDE.md", ".claude", ".codex", "memory", "rules")


@dataclass(frozen=True)
class PreparedCell:
    workspace: Path
    home: Path
    fixture_sha256: str
    environment: dict


def audit_clean_home(home):
    home = Path(home)
    present = [name for name in FORBIDDEN_CONTEXT if (home / name).exists()]
    if present:
        raise ValueError(f"host persistent context is present: {', '.join(present)}")
    return "absent"


def prepare_cell(manifest, cell, run_root):
    cell_root = safe_child(run_root, "cells", cell["cell_id"])
    workspace = cell_root / "workspace"
    home = cell_root / "home"
    if cell_root.exists():
        raise FileExistsError("cell root must not be reused")
    cell_root.mkdir(parents=True)
    home.mkdir()
    audit_clean_home(home)
    sealed = safe_child(run_root, "sealed-fixtures", cell["task_id"])
    reset_fixture(sealed, workspace)
    environment = {"HOME": str(home), "USERPROFILE": str(home),
                   "CODEX_HOME": str(home / ".codex"),
                   "CLAUDE_CONFIG_DIR": str(home / ".claude"),
                   "DITTO_HOME": str(home / ".ditto")}
    return PreparedCell(workspace, home, tree_hash(workspace), environment)


def execute_cell(manifest, cell, run_root, execute, approval):
    manifest_hash = sha256_bytes(canonical_bytes(manifest))
    if not execute:
        raise PermissionError("provider execution requires explicit approval")
    if approval != manifest_hash:
        raise PermissionError("approval must equal the exact manifest hash")
    prepared = prepare_cell(manifest, cell, run_root)
    system = next(item for item in manifest["systems"] if item["host"] == cell["host"])
    env = os.environ.copy()
    env.update(prepared.environment)
    completed = subprocess.run(system["run_argv"], cwd=prepared.workspace, env=env,
                               shell=False, capture_output=True, text=True,
                               timeout=cell["budget"]["time_seconds"])
    return prepared, completed
```

- [ ] **Step 4: Keep condition setup narrow and auditable**

Add a setup phase where `cold` receives no Ditto files and `ditto` invokes the manifest-captured, frozen v0.3.7 installation argv. Hash every installed skill/profile/instruction file before execution. Require identical repository task instructions, tools, permissions, budgets, and run argv within each pair. Fail if the dedicated home contains any other persistent context. Do not infer provider commands: `proof freeze-system` captures the exact live-tested argv and screenshot hash during the later cost preflight.

- [ ] **Step 5: Implement CLI modes**

`python -m proof.cli validate`, `freeze`, `prepare-cell`, `evaluate`, and `package` are read-only or local artifact operations. Only `execute-cell` accepts `--execute --approval`. The CLI must print JSON to stdout, errors to stderr, and nonzero exit codes on every failed gate.

Run: `python -m unittest tests.test_proof_runner -v`

Expected: execution remains disabled without both exact gates; subprocess mocks prove `shell=False` and isolated environment values.

- [ ] **Step 6: Commit the runner gate**

```bash
git add proof/runner.py proof/cli.py tests/test_proof_runner.py
git commit -m "feat: gate isolated proof execution"
```

### Task 7: Objective evaluation, hard failures, and independent review

**Files:**
- Create: `proof/evaluate.py`
- Test: `tests/test_proof_evaluate.py`

- [ ] **Step 1: Write failing tests for hard failures and reviewer eligibility**

```python
class EvaluationTest(unittest.TestCase):
    def test_fabricated_test_claim_is_hard_failure(self):
        record = objective_record(claimed_tests=True, test_report_sha256=None)
        result = evaluate_objective(record, task_policy("work"))
        self.assertIn("fabricated_test_result", result["hard_failures"])

    def test_operator_cannot_cast_blind_verdict(self):
        review = valid_review()
        review["reviewer_role"] = "operator"
        with self.assertRaisesRegex(ValueError, "independent third party"):
            validate_review(review, family="design")

    def test_writing_review_requires_unfamiliar_reviewer(self):
        review = valid_review()
        review["unfamiliar_with_operator_voice"] = False
        result = validate_review(review, family="write")
        self.assertEqual("invalid", result["status"])
        self.assertEqual("reviewer familiar with operator voice", result["invalidation_reason"])

    def test_blind_packet_contains_no_condition_system_path_or_order(self):
        packet = build_blind_pair(self.pair, self.outputs)
        encoded = json.dumps(packet).lower()
        for forbidden in ("cold", "ditto", "codex", "claude", "workspace", "order"):
            self.assertNotIn(forbidden, encoded)

    def test_reveal_maps_left_right_only_after_review(self):
        packet = build_blind_pair(self.pair, self.outputs)
        review = {"verdict": "left", "left_review_id": packet["left"]["review_id"],
                  "right_review_id": packet["right"]["review_id"]}
        self.assertIn(reveal_verdict(review, self.pair), ("cold", "ditto"))
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_proof_evaluate -v`

Expected: import failure for `proof.evaluate`.

- [ ] **Step 3: Implement objective and review contracts**

```python
# proof/evaluate.py
import math


def evaluate_objective(record, policy):
    failures = list(record.get("hard_failures", []))
    if record.get("claimed_tests") and not record.get("test_report_sha256"):
        failures.append("fabricated_test_result")
    if record.get("claimed_rendered_verification") and not record.get("rendered_artifact_sha256"):
        failures.append("fabricated_visual_verification")
    if record.get("changed_paths") and any(not path.startswith(tuple(policy["allowed_paths"])) for path in record["changed_paths"]):
        failures.append("out_of_scope_change")
    return {"checks": record["checks"], "hard_failures": sorted(set(failures)),
            "mechanism_checks": record.get("mechanism_checks", [])}


def validate_review(review, family):
    if review.get("reviewer_role") != "independent":
        raise ValueError("blind reviewer must be an independent third party")
    if not review.get("consent_reference") or not review.get("eligibility_attestation"):
        raise ValueError("review consent and eligibility are required")
    reason = ""
    if not review.get("blinding_confirmed"):
        reason = "condition-revealing context was visible"
    if family == "write" and not review.get("unfamiliar_with_operator_voice"):
        reason = "reviewer familiar with operator voice"
    if reason:
        return dict(review, status="invalid", verdict=None, invalidation_reason=reason)
    if review.get("verdict") not in ("left", "right", "tie"):
        raise ValueError("verdict must be left, right, or tie")
    return dict(review, status="valid", invalidation_reason="")


def build_blind_pair(pair, outputs_by_review_id):
    ordered = sorted(pair["cells"], key=lambda cell: cell["order"])
    sides = []
    for cell in ordered:
        output = outputs_by_review_id[cell["review_id"]]
        sides.append({"review_id": cell["review_id"],
                      "artifact_sha256": output["artifact_sha256"],
                      "output": output["sanitized_output"]})
    return {"schema": "ditto-proof-blind-pair/1", "family": ordered[0]["family"],
            "left": sides[0], "right": sides[1]}


def reveal_verdict(review, pair):
    if review["verdict"] == "tie":
        return "tie"
    key = "left_review_id" if review["verdict"] == "left" else "right_review_id"
    selected = review[key]
    matches = [cell for cell in pair["cells"] if cell["review_id"] == selected]
    if len(matches) != 1:
        raise ValueError("review ID is not in the frozen pair")
    return matches[0]["condition"]


def wilson_interval(successes, total, z=1.959963984540054):
    if total <= 0:
        return None
    center = (successes + z * z / 2) / (total + z * z)
    radius = z * math.sqrt((successes * (total - successes) / total) + z * z / 4) / (total + z * z)
    return [max(0.0, center - radius), min(1.0, center + radius)]
```

- [ ] **Step 4: Add family policy tests**

Work must catch regressions, destructive commands, secret exposure, out-of-scope changes, and completion without required verification. Design must catch excluded-surface changes, broken primary flow, failed accessibility floor, recolor-only output, and missing rendered artifact. Writing must catch unsupported facts/metrics, invented testimonials, false availability, privacy leaks, prohibited X formatting, spam pressure, and em dashes. Profile-rubric adherence is always labelled `mechanism_checks` and never a public standalone outcome. Blind packets expose only opaque review IDs, sanitized outputs, artifact hashes, and the family; condition, system identity, operator identity, run order, local paths, and metadata remain private until `reveal_verdict` maps a valid verdict back to the frozen pair.

Run: `python -m unittest tests.test_proof_evaluate -v`

Expected: all evaluator tests pass, including Wilson edge cases at zero and full successes.

- [ ] **Step 5: Commit evaluation rules**

```bash
git add proof/evaluate.py tests/test_proof_evaluate.py
git commit -m "feat: validate proof outcomes and blind reviews"
```

### Task 8: Fail-closed privacy scanning and sanitization

**Files:**
- Create: `proof/privacy.py`
- Test: `tests/test_proof_privacy.py`

- [ ] **Step 1: Write failing redaction-canary tests**

```python
class PrivacyTest(unittest.TestCase):
    def test_every_seeded_private_marker_blocks_packaging(self):
        markers = {
            "secret": "sk-proof-canary-1234567890",
            "username": "private-user-canary",
            "windows_path": r"C:\\Users\\private-canary\\vault",
            "unix_path": "/home/private-canary/vault",
            "profile": "PROFILE-CANARY-do-not-publish",
            "receipt": "RECEIPT-CANARY-do-not-publish",
        }
        for kind, marker in markers.items():
            with self.subTest(kind=kind):
                result = scan_public_text(f"safe before {marker} safe after", markers)
                self.assertFalse(result["passed"])
                self.assertIn(kind, result["findings"])

    def test_hebrew_round_trip_survives_when_safe(self):
        text = "תוצאה ציבורית בטוחה"
        self.assertEqual(text, sanitize_text(text, canaries={}))
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_proof_privacy -v`

Expected: import failure for `proof.privacy`.

- [ ] **Step 3: Implement canary, secret, path, and profile scanning**

```python
# proof/privacy.py
import re

SECRET_PATTERNS = (
    re.compile(r"\b(?:sk|ghp|github_pat)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b(?:api[_ -]?key|token|password)\s*[:=]\s*\S+"),
)
PATH_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\[^\s]*"),
    re.compile(r"/home/[^/\s]+/[^\s]*"),
)


def scan_public_text(text, canaries):
    findings = []
    for name, value in canaries.items():
        if value and value in text:
            findings.append(name)
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        findings.append("secret-pattern")
    if any(pattern.search(text) for pattern in PATH_PATTERNS):
        findings.append("local-path")
    return {"passed": not findings, "findings": sorted(set(findings))}


def sanitize_text(text, canaries):
    result = scan_public_text(text, canaries)
    if not result["passed"]:
        raise ValueError("privacy scan failed: " + ", ".join(result["findings"]))
    return text.encode("utf-8").decode("utf-8")
```

- [ ] **Step 4: Add package-tree privacy tests**

Require automated scanning of every filename and file body, plus a recorded manual-review approval. Reject symlinks, private-root path strings, raw transcripts, raw profiles, receipts, environment dumps, hidden files, unrecognized extensions, and any canary. Verify the public package contains hashes and sanitized excerpts only.

Run: `python -m unittest tests.test_proof_privacy -v`

Expected: all privacy tests pass and every seeded marker blocks packaging.

- [ ] **Step 5: Commit privacy gates**

```bash
git add proof/privacy.py tests/test_proof_privacy.py
git commit -m "feat: block private proof artifacts from publication"
```

### Task 9: Recalculate outcomes and generate a static package

**Files:**
- Create: `proof/publish.py`
- Test: `tests/test_proof_publish.py`

- [ ] **Step 1: Write failing aggregation and ship-gate tests**

```python
class PublishTest(unittest.TestCase):
    def test_preference_excludes_ties_and_keeps_tie_count(self):
        result = aggregate_preferences(["ditto", "cold", "tie", "ditto"])
        self.assertEqual({"ditto_wins": 2, "cold_wins": 1, "ties": 1, "binary_denominator": 3}, result["counts"])
        self.assertEqual(wilson_interval(2, 3), result["ditto_wilson_95"])

    def test_package_refuses_47_cells(self):
        with self.assertRaisesRegex(ValueError, "48 valid cells"):
            build_publication(manifest(), records(47), ship_approval="approved")

    def test_package_refuses_profile_rubric_as_headline(self):
        value = publication_fixture()
        value["headline_metric"] = "profile_rubric_adherence"
        with self.assertRaisesRegex(ValueError, "mechanism only"):
            validate_publication(value)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_proof_publish -v`

Expected: import failure for `proof.publish`.

- [ ] **Step 3: Implement deterministic recalculation and package generation**

```python
# proof/publish.py
import html
from pathlib import Path

from proof.canonical import canonical_bytes, sha256_bytes, write_once_json
from proof.evaluate import wilson_interval
from proof.privacy import sanitize_text


def aggregate_preferences(verdicts):
    counts = {"ditto_wins": verdicts.count("ditto"), "cold_wins": verdicts.count("cold"),
              "ties": verdicts.count("tie")}
    counts["binary_denominator"] = counts["ditto_wins"] + counts["cold_wins"]
    return {"counts": counts,
            "ditto_wilson_95": wilson_interval(counts["ditto_wins"], counts["binary_denominator"])}


def build_publication(manifest, records, ship_approval):
    valid = [record for record in records if record["publication_status"] == "eligible"]
    if len(valid) != 48:
        raise ValueError("Ditto Proof v1 requires 48 valid cells")
    if ship_approval != sha256_bytes(canonical_bytes({"manifest": manifest, "records": valid})):
        raise PermissionError("ship approval must match the exact evidence digest")
    return {"schema": "ditto-proof-publication/1", "label": "small-n, directional only",
            "cells": valid, "limitations": manifest["limitations"],
            "exclusions": [item for item in records if item["publication_status"] != "eligible"]}


def render_index(publication, destination, canaries):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    title = sanitize_text("Ditto Proof v1", canaries)
    body = "<!doctype html><meta charset='utf-8'><title>{0}</title><h1>{0}</h1><p>Small-n, directional only.</p>".format(html.escape(title))
    (destination / "index.html").write_text(body, encoding="utf-8", newline="\n")
    write_once_json(destination / "results.json", publication)
```

- [ ] **Step 4: Add complete public-outcome tests**

Recalculate blind win/tie/loss counts, hard failures by condition, raw denominators, invalidations, exclusions, retry history, unavailable systems, descriptive duration/usage only when comparable, and per-cell artifact hashes. Writing preference must be omitted when reviewer eligibility fails. Output must say complete-system comparison, clean-host cold start, and small-n directional only; it must contain no p-values, significance language, model ranking, `1000x`, or traffic/star forecasts.

Run: `python -m unittest tests.test_proof_publish -v`

Expected: all publication tests pass and two runs from identical records are byte-identical.

- [ ] **Step 5: Commit publication generation**

```bash
git add proof/publish.py tests/test_proof_publish.py
git commit -m "feat: generate sanitized Ditto Proof evidence"
```

### Task 10: Add the six-execution non-scored pilot

**Files:**
- Create: `proof/fixtures/pilot/work/`
- Create: `proof/fixtures/pilot/design/`
- Create: `proof/fixtures/pilot/write/`
- Create: `proof/fixtures/pilot/registry.json`
- Test: `tests/test_proof_pilot.py`

- [ ] **Step 1: Write failing pilot separation tests**

```python
class PilotFixtureTest(unittest.TestCase):
    def test_pilot_has_three_non_scored_families(self):
        registry = json.loads((ROOT / "proof/fixtures/pilot/registry.json").read_text("utf-8"))
        self.assertEqual({"work", "design", "write"}, {item["family"] for item in registry["tasks"]})
        self.assertTrue(all(item["scored"] is False for item in registry["tasks"]))
        self.assertTrue(all(item["task_id"].startswith("pilot-") for item in registry["tasks"]))

    def test_pilot_ids_cannot_enter_v1_matrix(self):
        with self.assertRaisesRegex(ValueError, "pilot fixture"):
            build_pairs(self.systems, {"work-primary": "a" * 64, "work-held-out": "b" * 64,
                                      "design-primary": "c" * 64, "design-held-out": "d" * 64,
                                      "write-primary": "e" * 64, "write-held-out": "f" * 64,
                                      "pilot-work": "0" * 64}, self.seed)
```

- [ ] **Step 2: Create deterministic pilot fixtures**

The work pilot is a tiny stdlib Python repository with a scoped failing test, an unrelated passing module, and a machine-readable `checks.json`. The design pilot is a single-page local HTML fixture with one named card surface, keyboard-flow checks, a fixed 1280x720 render target, and required screenshot/accessibility report paths. The writing pilot contains a fictional product fact packet, an X audience/channel constraint, a 240-character ceiling, prohibited unsupported claims, and a machine-readable output contract. None uses Ohad, Ditto, real product facts, or either scored fixture.

- [ ] **Step 3: Add pilot gate integration tests**

Simulate cold and Ditto records for all three pilot families. Assert six executions, deterministic resets, different cell roots, opaque review IDs, complete required fields, caught redaction canaries, objective-check capture, blind-review capture, and a sanitized package labelled `pilot`, `non-scored`, and `non-comparable`.

Run: `python -m unittest tests.test_proof_pilot -v`

Expected: pilot integration passes without running a provider or touching `ditto.py`.

- [ ] **Step 4: Commit pilot fixtures**

```bash
git add proof/fixtures/pilot tests/test_proof_pilot.py
git commit -m "test: add isolated non-scored proof pilot"
```

### Task 11: Document private fixture authoring, cost freeze, review, and ship gates

**Files:**
- Create: `docs/proof/README.md`
- Create: `docs/proof/example-publication/index.html`
- Create: `docs/proof/example-publication/results.json`
- Modify: `.gitignore`
- Modify: `README.md`
- Test: `tests/test_proof_docs.py`

- [ ] **Step 1: Write documentation truth tests**

```python
class ProofDocumentationTest(unittest.TestCase):
    def test_runbook_preserves_every_gate(self):
        text = (ROOT / "docs/proof/README.md").read_text("utf-8")
        required = (
            "48 isolated cell executions", "clean-host cold start",
            "small-n, directional only", "independent third party",
            "Ohad cannot cast a blind verdict", "explicit cost approval",
            "explicit ship approval", "v0.3.7", "held-out",
            "private run root outside the repository",
        )
        for phrase in required:
            self.assertIn(phrase, text)

    def test_docs_make_no_result_claim_before_execution(self):
        text = (ROOT / "README.md").read_text("utf-8") + (ROOT / "docs/proof/README.md").read_text("utf-8")
        self.assertNotIn("Ditto wins", text)
        self.assertNotIn("statistically significant", text)
```

- [ ] **Step 2: Write the operator runbook**

Document exact commands for `validate`, private fixture sealing, live system capture, matrix freeze, expected-cost/quota recording, explicit approval digest, pilot preparation, cell execution, artifact recording, independent review, privacy scan, aggregate recalculation, and separate evidence-digest ship approval. State that provider commands and current labels come from observed provider interfaces, unavailable systems are not substituted, both attempts are retained, and the run stops on mixed versions or contamination.

The fixture-authoring section must specify the required six private task IDs, family-specific `brief.md`, `policy.json`, `checks.json`, starting files, and deterministic success commands. It must forbid storing the content in Git before execution and require both variants to be frozen before the pilot. This is an operational input contract, not an invitation to tune tasks after outputs are visible.

- [ ] **Step 3: Add consent and blind-review forms**

Include exact JSON examples for reviewer consent reference, eligibility attestation, unfamiliarity with Ohad/voice, blinding confirmation, anonymous verdict publication, and invalidation. State that recognizing the operator or condition ends the review and records an invalid verdict.

- [ ] **Step 4: Add publication and media gates**

Document that the generated example is synthetic. Real evidence, clips, README claims, website changes, launch copy, and a benchmark GitHub release require all 48 cells or an explicitly non-v1 label, passing privacy review, recomputed numbers, limitations, and Ohad's separate evidence-digest approval. Clips must trace to exact cell hashes and cannot hide losses.

- [ ] **Step 5: Protect local run roots and link methodology**

Append these ignore entries:

```gitignore
# Ditto Proof private fixtures, profiles, reviewer records, and run artifacts
.ditto-proof-private/
proof-private/
ditto-proof-runs/
```

Add one README sentence linking to `docs/proof/README.md` and describing it as an unexecuted methodology until a separately approved evidence release exists.

Run: `python -m unittest tests.test_proof_docs -v`

Expected: documentation tests pass with no benchmark outcome claim.

- [ ] **Step 6: Commit the runbook**

```bash
git add .gitignore README.md docs/proof tests/test_proof_docs.py
git commit -m "docs: add Ditto Proof v1 runbook"
```

### Task 12: End-to-end verification without provider execution

**Files:**
- Modify: `tests/test_proof_pilot.py`
- Create: `docs/proof/implementation-verification.md`

- [ ] **Step 1: Add a full synthetic dry-run test**

The test creates an external temporary run root, seals six synthetic v1 fixtures, freezes one Codex-host and one Claude-host system with harmless Python subprocess argv, builds 24 pairs, prepares 48 unique cells, records synthetic attempts/evaluations/reviews, verifies every hash, catches a seeded leak in a rejected package, and generates a clean byte-deterministic 48-cell package after an exact evidence-digest approval.

- [ ] **Step 2: Prove normal Ditto remains independent**

Run: `python -m unittest discover -s tests -v`

Expected: the full existing suite plus all proof tests pass. No proof module is imported by `ditto.py`; no test writes to the real Ditto profile home; no provider process runs.

- [ ] **Step 3: Run repository integrity checks**

Run: `git diff --check`

Expected: no output and exit code 0.

Run: `git status --short`

Expected: only the intended proof implementation and verification document are present before the final commit.

- [ ] **Step 4: Record observed verification**

Write `docs/proof/implementation-verification.md` with the exact commit, Python version, operating system, test command, test count, duration, pilot-package hash, and explicit boundaries: no provider execution, no scored fixture execution, no public result, no Antigravity dependency, and no modification to normal Ditto behavior.

- [ ] **Step 5: Commit verified harness**

```bash
git add proof tests docs/proof .gitignore README.md
git commit -m "feat: complete disabled Ditto Proof v1 harness"
```

- [ ] **Step 6: Stop at the implementation handoff gate**

Do not select systems, incur provider cost, recruit a reviewer, run the scored fixtures, generate real proof clips, push public claims, or publish a benchmark release. Present the verified harness and the live preflight fields still requiring Ohad's explicit choices and cost approval.

## Self-review checklist

- Every approved design requirement maps to a task above: frozen tuple and matrix (Tasks 2 and 4), private fixtures and isolation (Tasks 3 and 6), append-only evidence and retry policy (Task 5), objective/blind outcomes and uncertainty (Tasks 7 and 9), privacy and consent (Tasks 8 and 11), pilot gate (Task 10), publication/claim gates (Tasks 9 and 11), and regression verification (Task 12).
- Pattern Commons, Antigravity, full Operator OS work, billing, outreach automation, Atlas, and provider purchases remain outside this plan.
- Runtime-varying evidence such as provider menu labels, exact model IDs, host versions, argv, screenshots, quota, cost, reviewer consent, and ship approval is captured through strict schemas and hashes; the plan does not invent it.
- Primary and held-out scored fixture content is never embedded in this committed plan, preserving the approved concealment rule. The private authoring contract and freeze timing are explicit.
- Function names remain consistent across tasks: `canonical_bytes`, `safe_child`, `write_once_json`, `seal_fixture`, `reset_fixture`, `build_system_freeze`, `build_pairs`, `EvidenceStore`, `prepare_cell`, `execute_cell`, `evaluate_objective`, `validate_review`, `build_blind_pair`, `reveal_verdict`, `wilson_interval`, `scan_public_text`, `aggregate_preferences`, and `build_publication`.
