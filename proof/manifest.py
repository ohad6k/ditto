"""Freeze live system identity and construct the exact Ditto Proof v1 matrix."""

import hashlib
import random

from proof import (
    BENCHMARK_NAME,
    BENCHMARK_SCHEMA,
    CONDITIONS,
    DITTO_COMMIT,
    DITTO_REF,
    FAMILIES,
    TRIALS,
    VARIANTS,
)
from proof.canonical import canonical_bytes
from proof.schema import UNCERTAINTY_POLICY, require_sha256, validate_manifest


TASK_IDS = tuple(f"{family}-{variant}" for family in FAMILIES for variant in VARIANTS)


def stable_id(prefix, value):
    return f"{prefix}-{hashlib.sha256(canonical_bytes(value)).hexdigest()[:20]}"


def _require_argv(value, label):
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise ValueError(f"{label} must be a nonempty argv list")


def build_system_freeze(
    host,
    menu_label,
    model_id,
    host_version,
    run_argv,
    ditto_install_argv,
    screenshot_sha256,
    tool_policy_sha256,
    permission_policy_sha256,
    quota_snapshot,
    expected_cost,
):
    """Create one exact, live-captured complete-system identity."""
    if host not in ("codex", "claude"):
        raise ValueError("host must be codex or claude")
    if not isinstance(menu_label, str) or not menu_label.strip():
        raise ValueError("menu label is required")
    lowered = menu_label.casefold()
    if any(marker in lowered for marker in ("mini", "preview", "fast")):
        raise ValueError("ineligible system label")
    if model_id is not None and (not isinstance(model_id, str) or not model_id):
        raise ValueError("model ID must be text or null")
    if not isinstance(host_version, str) or not host_version:
        raise ValueError("host version is required")
    _require_argv(run_argv, "run_argv")
    _require_argv(ditto_install_argv, "ditto_install_argv")
    for digest, label in (
        (screenshot_sha256, "selection_screenshot_sha256"),
        (tool_policy_sha256, "tool_policy_sha256"),
        (permission_policy_sha256, "permission_policy_sha256"),
    ):
        require_sha256(digest, label)
    if not isinstance(quota_snapshot, str) or not quota_snapshot.strip():
        raise ValueError("quota snapshot is required")
    if not isinstance(expected_cost, str) or not expected_cost.strip():
        raise ValueError("expected cost is required")

    identity = {
        "host": host,
        "menu_label": menu_label,
        "model_id": model_id,
        "host_version": host_version,
        "run_argv": list(run_argv),
        "ditto_install_argv": list(ditto_install_argv),
        "selection_screenshot_sha256": screenshot_sha256,
        "tool_policy_sha256": tool_policy_sha256,
        "permission_policy_sha256": permission_policy_sha256,
        "quota_snapshot": quota_snapshot,
        "expected_cost": expected_cost,
    }
    return {"system_id": stable_id("system", identity), **identity}


def _validate_matrix_inputs(
    systems,
    fixture_hashes,
    instruction_hashes,
    profile_manifest_sha256,
    budgets,
    seed,
):
    if len(systems) != 2 or {item.get("host") for item in systems} != {
        "codex",
        "claude",
    }:
        raise ValueError("v1 requires one Codex-host and one Claude-host system")
    if len({item.get("system_id") for item in systems}) != 2:
        raise ValueError("system identities must be unique")
    if any(task_id.startswith("pilot-") for task_id in fixture_hashes):
        raise ValueError("pilot fixture cannot enter the v1 matrix")
    if set(fixture_hashes) != set(TASK_IDS):
        raise ValueError("v1 requires the exact six fixture IDs")
    if set(instruction_hashes) != set(TASK_IDS):
        raise ValueError("v1 requires the exact six instruction IDs")
    if set(budgets) != set(FAMILIES):
        raise ValueError("v1 requires one frozen budget per family")
    for task_id in TASK_IDS:
        require_sha256(fixture_hashes[task_id], f"{task_id} fixture")
        require_sha256(instruction_hashes[task_id], f"{task_id} instruction")
    require_sha256(profile_manifest_sha256, "profile_manifest_sha256")
    require_sha256(seed, "matrix seed")


def build_pairs(
    systems,
    fixture_hashes,
    instruction_hashes,
    profile_manifest_sha256,
    budgets,
    seed,
):
    """Build exactly 24 frozen pairs and 48 isolated condition cells."""
    _validate_matrix_inputs(
        systems,
        fixture_hashes,
        instruction_hashes,
        profile_manifest_sha256,
        budgets,
        seed,
    )
    pairs = []
    for system in systems:
        for family in FAMILIES:
            budget = budgets[family]
            if (
                not isinstance(budget, dict)
                or not isinstance(budget.get("time_seconds"), int)
                or budget["time_seconds"] <= 0
                or not isinstance(budget.get("max_turns"), int)
                or budget["max_turns"] <= 0
            ):
                raise ValueError(f"invalid {family} budget")
            for variant in VARIANTS:
                task_id = f"{family}-{variant}"
                for trial in TRIALS:
                    base = {
                        "system_id": system["system_id"],
                        "host": system["host"],
                        "task_id": task_id,
                        "family": family,
                        "variant": variant,
                        "trial": trial,
                        "fixture_sha256": fixture_hashes[task_id],
                        "instruction_sha256": instruction_hashes[task_id],
                        "tool_policy_sha256": system["tool_policy_sha256"],
                        "permission_policy_sha256": system[
                            "permission_policy_sha256"
                        ],
                        "budget": dict(budget),
                    }
                    pair_id = stable_id("pair", base)
                    order = list(CONDITIONS)
                    random.Random(f"{seed}:{pair_id}").shuffle(order)
                    cells = []
                    for index, condition in enumerate(order, start=1):
                        private_identity = {
                            "pair_id": pair_id,
                            "condition": condition,
                        }
                        cells.append(
                            {
                                **base,
                                "pair_id": pair_id,
                                "condition": condition,
                                "order": index,
                                "cell_id": stable_id("cell", private_identity),
                                "review_id": stable_id(
                                    "review",
                                    {**private_identity, "seed": seed},
                                ),
                                "profile_manifest_sha256": (
                                    profile_manifest_sha256
                                    if condition == "ditto"
                                    else None
                                ),
                                "host_persistent_context": "absent",
                            }
                        )
                    pairs.append({"pair_id": pair_id, **base, "cells": cells})
    if len(pairs) != 24:
        raise AssertionError("matrix construction did not produce 24 pairs")
    return pairs


def build_manifest(
    systems,
    pairs,
    profile_manifest_sha256,
    private_rubric_sha256,
    public_rubric_sha256,
    limitations,
    created_at,
):
    value = {
        "schema": BENCHMARK_SCHEMA,
        "benchmark": BENCHMARK_NAME,
        "benchmark_version": "1.0.0",
        "ditto_ref": DITTO_REF,
        "ditto_commit": DITTO_COMMIT,
        "profile_manifest_sha256": profile_manifest_sha256,
        "private_rubric_sha256": private_rubric_sha256,
        "public_rubric_sha256": public_rubric_sha256,
        "uncertainty_policy": UNCERTAINTY_POLICY,
        "host_persistent_context": "absent",
        "systems": systems,
        "pairs": pairs,
        "limitations": limitations,
        "created_at": created_at,
    }
    return validate_manifest(value)
