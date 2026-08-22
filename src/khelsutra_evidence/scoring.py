"""Deterministic reference scoring for rally boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .schemas import JsonObject
from .validation import validate_document


@dataclass(frozen=True)
class _Cell:
    matches: int
    error: int
    action: Literal["match", "skip_truth", "skip_prediction", "done"]


def _better(candidates: list[_Cell]) -> _Cell:
    priority = {"match": 0, "skip_prediction": 1, "skip_truth": 2, "done": 3}
    return min(candidates, key=lambda cell: (-cell.matches, cell.error, priority[cell.action]))


def score_rallies(truth: JsonObject, prediction: JsonObject, tolerance_frames: int) -> JsonObject:
    _require_valid_set(truth, "truth")
    _require_valid_set(prediction, "prediction")
    if tolerance_frames < 0:
        raise ValueError("tolerance_frames must be non-negative")
    if truth["sample_id"] != prediction["sample_id"]:
        raise ValueError("truth and prediction sample_id values differ")
    if abs(float(truth["fps"]) - float(prediction["fps"])) > 1e-9:
        raise ValueError("truth and prediction fps values differ")

    truths = sorted(truth["rallies"], key=_rally_key)
    predictions = sorted(prediction["rallies"], key=_rally_key)
    n, m = len(truths), len(predictions)
    dp = [[_Cell(0, 0, "done") for _ in range(m + 1)] for _ in range(n + 1)]

    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            candidates: list[_Cell] = []
            if i < n:
                child = dp[i + 1][j]
                candidates.append(_Cell(child.matches, child.error, "skip_truth"))
            if j < m:
                child = dp[i][j + 1]
                candidates.append(_Cell(child.matches, child.error, "skip_prediction"))
            if i < n and j < m:
                start_error = abs(
                    int(truths[i]["start_frame"]) - int(predictions[j]["start_frame"])
                )
                end_error = abs(int(truths[i]["end_frame"]) - int(predictions[j]["end_frame"]))
                same_court = truths[i]["target_court_id"] == predictions[j]["target_court_id"]
                if same_court and start_error <= tolerance_frames and end_error <= tolerance_frames:
                    child = dp[i + 1][j + 1]
                    candidates.append(
                        _Cell(child.matches + 1, child.error + start_error + end_error, "match")
                    )
            dp[i][j] = _better(candidates)

    matches: list[dict[str, Any]] = []
    unmatched_truth: list[str] = []
    unmatched_prediction: list[str] = []
    i = j = 0
    while i < n or j < m:
        action = dp[i][j].action
        if action == "match":
            truth_rally, predicted_rally = truths[i], predictions[j]
            matches.append(
                {
                    "truth_id": truth_rally["rally_id"],
                    "prediction_id": predicted_rally["rally_id"],
                    "start_error_frames": abs(
                        int(truth_rally["start_frame"]) - int(predicted_rally["start_frame"])
                    ),
                    "end_error_frames": abs(
                        int(truth_rally["end_frame"]) - int(predicted_rally["end_frame"])
                    ),
                }
            )
            i += 1
            j += 1
        elif action == "skip_truth":
            unmatched_truth.append(truths[i]["rally_id"])
            i += 1
        elif action == "skip_prediction":
            unmatched_prediction.append(predictions[j]["rally_id"])
            j += 1
        else:
            raise RuntimeError("scoring trace ended before all rallies were consumed")

    matched = len(matches)
    precision = matched / m if m else 1.0 if n == 0 else 0.0
    recall = matched / n if n else 1.0 if m == 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    mean_start = sum(item["start_error_frames"] for item in matches) / matched if matched else None
    mean_end = sum(item["end_error_frames"] for item in matches) / matched if matched else None
    return {
        "schema_name": "RallyScoreV1",
        "schema_version": "1.0.0",
        "record_id": f"score-{truth['sample_id']}",
        "sample_id": truth["sample_id"],
        "tolerance_frames": tolerance_frames,
        "truth_count": n,
        "prediction_count": m,
        "matched_count": matched,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_start_error_frames": mean_start,
        "mean_end_error_frames": mean_end,
        "matches": matches,
        "unmatched_truth_ids": unmatched_truth,
        "unmatched_prediction_ids": unmatched_prediction,
    }


def _rally_key(rally: JsonObject) -> tuple[str, int, int, str]:
    return (
        str(rally["target_court_id"]),
        int(rally["start_frame"]),
        int(rally["end_frame"]),
        str(rally["rally_id"]),
    )


def _require_valid_set(document: JsonObject, expected_role: str) -> None:
    issues = validate_document(document)
    if issues:
        raise ValueError("invalid rally set: " + "; ".join(issue.render() for issue in issues))
    if document["schema_name"] != "RallyBoundarySetV1":
        raise ValueError("score inputs must use RallyBoundarySetV1")
    if document["role"] != expected_role:
        raise ValueError(f"expected {expected_role!r} role, got {document['role']!r}")
