from __future__ import annotations

import pytest

from khelsutra_evidence.comparison import compare_runs
from khelsutra_evidence.validation import validate_document


def test_example_runs_are_paired_for_quality_only(load_example) -> None:
    result = compare_runs(load_example("runs/system-a.json"), load_example("runs/system-b.json"))
    assert result["verdict"] == "paired_quality_only"
    assert result["quality_comparable"] is True
    assert result["cost_comparable"] is False
    assert validate_document(result) == []


def test_fully_paired_when_both_cost_receipts_exist(load_example) -> None:
    left = load_example("runs/system-a.json")
    right = load_example("runs/system-b.json")
    right["cost_receipt"] = left["cost_receipt"]
    assert compare_runs(left, right)["verdict"] == "paired"


def test_partial_for_sample_or_stratum_difference(load_example) -> None:
    left = load_example("runs/system-a.json")
    right = load_example("runs/system-b.json")
    right["samples"].append({"sample_id": "synthetic-match-002", "status": "accepted"})
    right["scenario_strata"] = ["single-clean"]
    result = compare_runs(left, right)
    assert result["verdict"] == "partially_comparable"
    # three comparability reasons, plus the operation-mode disclosure every report now carries
    assert len(result["reasons"]) == 4


def test_descriptive_when_no_samples_overlap(load_example) -> None:
    left = load_example("runs/system-a.json")
    right = load_example("runs/system-b.json")
    right["samples"][0]["sample_id"] = "different-match"
    assert compare_runs(left, right)["verdict"] == "descriptive_only"


def test_incompatible_when_task_contract_differs(load_example) -> None:
    left = load_example("runs/system-a.json")
    right = load_example("runs/system-b.json")
    right["task_contract"]["scorer_version"] = "2.0.0"
    result = compare_runs(left, right)
    assert result["verdict"] == "incompatible"
    assert result["cost_comparable"] is False


def test_compare_rejects_invalid_or_wrong_document(load_example) -> None:
    with pytest.raises(ValueError, match="invalid left"):
        compare_runs({}, load_example("runs/system-b.json"))
    with pytest.raises(ValueError, match="SystemRunV1"):
        compare_runs(load_example("scenario-profile.json"), load_example("runs/system-b.json"))
