"""Non-scored six-cell calibration pilot for the proof harness."""

import json
from pathlib import Path

from proof.canonical import canonical_bytes, sha256_bytes
from proof.fixtures import tree_hash
from proof.privacy import sanitize_text


FAMILIES = ("work", "design", "write")
CONDITIONS = ("cold", "emulo")


def load_pilot_registry(path):
    path = Path(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "emulo-proof-pilot-registry/1":
        raise ValueError("unsupported pilot registry")
    tasks = value.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 3:
        raise ValueError("pilot registry requires exactly three tasks")
    if {item.get("family") for item in tasks} != set(FAMILIES):
        raise ValueError("pilot registry requires work, design, and write")
    for item in tasks:
        if item.get("scored") is not False or not item.get("task_id", "").startswith(
            "pilot-"
        ):
            raise ValueError("pilot tasks must be explicitly non-scored")
        fixture = path.parent / item["path"]
        if tree_hash(fixture) != item.get("fixture_sha256"):
            raise ValueError("pilot fixture hash mismatch")
        contract = fixture / item["contract"]
        if not contract.is_file():
            raise ValueError("pilot contract is missing")
    return value


def _opaque_id(prefix, value):
    return f"{prefix}-{sha256_bytes(canonical_bytes(value))[:20]}"


def build_pilot_plan(registry, seed):
    if not isinstance(seed, str) or not seed:
        raise ValueError("pilot seed is required")
    cells = []
    for task in sorted(registry["tasks"], key=lambda item: item["family"]):
        pair_id = _opaque_id(
            "pilot-pair",
            {"seed": seed, "task_id": task["task_id"], "fixture": task["fixture_sha256"]},
        )
        for condition in CONDITIONS:
            identity = {"pair_id": pair_id, "condition": condition, "seed": seed}
            cells.append(
                {
                    "cell_id": _opaque_id("pilot-cell", identity),
                    "pair_id": pair_id,
                    "review_id": _opaque_id("review", {**identity, "blind": True}),
                    "task_id": task["task_id"],
                    "family": task["family"],
                    "condition": condition,
                    "fixture_sha256": task["fixture_sha256"],
                    "scored": False,
                }
            )
    if len(cells) != 6:
        raise AssertionError("pilot plan must contain six cells")
    return cells


def build_pilot_package(records, canaries, private_roots=()):
    records = sorted(list(records), key=lambda item: item.get("cell_id", ""))
    if len(records) != 6 or len({item.get("cell_id") for item in records}) != 6:
        raise ValueError("pilot package requires six unique executions")
    if {item.get("family") for item in records} != set(FAMILIES):
        raise ValueError("pilot package is missing a family")
    if any(item.get("scored") is not False for item in records):
        raise ValueError("pilot records must remain non-scored")
    for item in records:
        if not item.get("objective_checks") or not item.get("blind_review"):
            raise ValueError("pilot capture is incomplete")
        if item.get("redaction_state") != "passed":
            raise ValueError("pilot redaction must pass")
    package = {
        "schema": "emulo-proof-pilot/1",
        "label": "pilot",
        "scored": False,
        "comparable": False,
        "execution_count": 6,
        "limitations": ["non-scored", "non-comparable", "no provider result"],
        "records": records,
    }
    sanitize_text(
        canonical_bytes(package).decode("ascii"),
        canaries,
        private_roots,
    )
    return package
