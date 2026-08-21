from __future__ import annotations

import pytest

from khelsutra_evidence.scoring import score_rallies
from khelsutra_evidence.validation import validate_document


def test_reference_score_is_deterministic_and_valid(load_example) -> None:
    result = score_rallies(
        load_example("rallies/truth.json"), load_example("rallies/prediction.json"), 15
    )
    assert result["matched_count"] == 2
    assert result["f1"] == pytest.approx(2 / 3)
    assert result["unmatched_truth_ids"] == ["truth-rally-003"]
    assert result["unmatched_prediction_ids"] == ["prediction-rally-fp"]
    assert validate_document(result) == []


def test_reference_score_prefers_lowest_total_error(load_example) -> None:
    truth = load_example("rallies/truth.json")
    prediction = load_example("rallies/prediction.json")
    truth["rallies"] = [truth["rallies"][0]]
    prediction["rallies"] = [
        {
            **prediction["rallies"][0],
            "rally_id": "prediction-best",
            "start_frame": 0,
            "end_frame": 50,
        },
        {
            **prediction["rallies"][0],
            "rally_id": "prediction-worse",
            "start_frame": 300,
            "end_frame": 350,
        },
    ]
    result = score_rallies(truth, prediction, 250)
    assert result["matches"][0]["prediction_id"] == "prediction-best"


def test_empty_sets_score_perfectly_when_both_empty(load_example) -> None:
    truth = load_example("rallies/truth.json")
    prediction = load_example("rallies/prediction.json")
    truth["rallies"] = []
    prediction["rallies"] = []
    result = score_rallies(truth, prediction, 0)
    assert result["precision"] == result["recall"] == result["f1"] == 1.0


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda truth, prediction: prediction.update(sample_id="other-sample"), "sample_id"),
        (lambda truth, prediction: prediction.update(fps=60), "fps"),
        (lambda truth, prediction: prediction.update(role="truth"), "expected 'prediction'"),
    ],
)
def test_score_rejects_incompatible_inputs(load_example, mutation, message: str) -> None:
    truth = load_example("rallies/truth.json")
    prediction = load_example("rallies/prediction.json")
    mutation(truth, prediction)
    with pytest.raises(ValueError, match=message):
        score_rallies(truth, prediction, 15)


def test_score_rejects_negative_tolerance_and_wrong_schema(load_example) -> None:
    truth = load_example("rallies/truth.json")
    prediction = load_example("rallies/prediction.json")
    with pytest.raises(ValueError, match="non-negative"):
        score_rallies(truth, prediction, -1)
    truth = load_example("scenario-profile.json")
    with pytest.raises(ValueError, match="RallyBoundarySetV1"):
        score_rallies(truth, prediction, 15)
