"""Rationale-backed comparability verdicts for system runs."""

from __future__ import annotations

import hashlib

from .schemas import JsonObject
from .validation import validate_document


def compare_runs(left: JsonObject, right: JsonObject) -> JsonObject:
    _require_run(left, "left")
    _require_run(right, "right")

    left_task = left["task_contract"]
    right_task = right["task_contract"]
    incompatible_fields = [
        field
        for field in (
            "task_id",
            "prediction_unit",
            "boundary_tolerance_frames",
            "scorer_name",
            "scorer_version",
        )
        if left_task.get(field) != right_task.get(field)
    ]
    left_samples = {sample["sample_id"] for sample in left["samples"]}
    right_samples = {sample["sample_id"] for sample in right["samples"]}
    shared = sorted(left_samples & right_samples)
    left_only = sorted(left_samples - right_samples)
    right_only = sorted(right_samples - left_samples)
    strata_equal = set(left["scenario_strata"]) == set(right["scenario_strata"])
    cost_comparable = "cost_receipt" in left and "cost_receipt" in right

    reasons: list[str] = []
    if incompatible_fields:
        verdict = "incompatible"
        reasons.append("task contract differs: " + ", ".join(incompatible_fields))
        quality_comparable = False
        cost_comparable = False
    elif not shared:
        verdict = "descriptive_only"
        reasons.append("task contract matches but the runs share no sample IDs")
        quality_comparable = False
        cost_comparable = False
    elif left_only or right_only or not strata_equal:
        verdict = "partially_comparable"
        quality_comparable = True
        if left_only or right_only:
            reasons.append("only a strict subset of sample IDs is shared")
        if not strata_equal:
            reasons.append("scenario strata differ")
        if not cost_comparable:
            reasons.append("one or both runs omit a cost receipt")
    elif not cost_comparable:
        verdict = "paired_quality_only"
        quality_comparable = True
        reasons.append("task, scorer, samples, and strata match; cost evidence is incomplete")
    else:
        verdict = "paired"
        quality_comparable = True
        reasons.append("task, scorer, samples, strata, and cost evidence are compatible")

    identity = hashlib.sha256(f"{left['run_id']}\0{right['run_id']}".encode()).hexdigest()[:20]
    return {
        "schema_name": "ComparisonReportV1",
        "schema_version": "1.0.0",
        "record_id": f"comparison-{identity}",
        "left_run_id": left["run_id"],
        "right_run_id": right["run_id"],
        "verdict": verdict,
        "reasons": reasons,
        "shared_sample_ids": shared,
        "left_only_sample_ids": left_only,
        "right_only_sample_ids": right_only,
        "quality_comparable": quality_comparable,
        "cost_comparable": cost_comparable,
        "scenario_strata_equal": strata_equal,
    }


def _require_run(document: JsonObject, label: str) -> None:
    issues = validate_document(document)
    if issues:
        raise ValueError(f"invalid {label} run: " + "; ".join(issue.render() for issue in issues))
    if document["schema_name"] != "SystemRunV1":
        raise ValueError(f"{label} input must use SystemRunV1")
