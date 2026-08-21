from __future__ import annotations

import json
from pathlib import Path

import pytest

from khelsutra_evidence.schemas import load_schemas, schemas_by_name, validator_for
from khelsutra_evidence.validation import (
    canonical_recipe_digest,
    load_json,
    safety_issues,
    validate_document,
    validate_path,
)


def _messages(document: dict[str, object]) -> list[str]:
    return [issue.render() for issue in validate_document(document)]


def test_all_synthetic_examples_validate(examples_root: Path) -> None:
    assert validate_path(examples_root) == {}
    assert len(schemas_by_name()) == 16
    assert len(load_schemas()) == 17


def test_load_json_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level"):
        load_json(path)


def test_unknown_or_missing_schema_is_rejected() -> None:
    assert "missing string schema_name" in _messages({})[0]
    assert "unknown schema" in _messages({"schema_name": "NoSuchSchema"})[0]
    with pytest.raises(ValueError, match="unknown schema_name"):
        validator_for("NoSuchSchema")


def test_scenario_active_games_cannot_exceed_visible(load_example) -> None:
    document = load_example("scenario-profile.json")
    document["simultaneously_active_games"] = 4
    assert any("cannot exceed" in message for message in _messages(document))


def test_commercialization_overall_is_derived(load_example) -> None:
    document = load_example("commercialization-readiness.json")
    document["overall_status"] = "verified_clear"
    assert any("must be 'restricted'" in message for message in _messages(document))


def test_cost_raw_math_and_accepted_bounds(load_example) -> None:
    document = load_example("cost-receipt.json")
    document["accepted_source_seconds"] = 700
    document["inference_usd_per_source_hour"] = 9
    messages = _messages(document)
    assert any("cannot exceed" in message for message in messages)
    assert any("raw numerator/denominator" in message for message in messages)


def test_rally_ids_order_and_overlap_are_checked(load_example) -> None:
    document = load_example("rallies/truth.json")
    document["rallies"][1]["rally_id"] = document["rallies"][0]["rally_id"]
    document["rallies"][1]["start_frame"] = 200
    document["rallies"][2]["end_frame"] = document["rallies"][2]["start_frame"]
    messages = _messages(document)
    assert any("must be unique" in message for message in messages)
    assert any("must not overlap" in message for message in messages)
    assert any("must be after" in message for message in messages)


def test_system_run_requires_unique_samples_and_failure_disclosure(load_example) -> None:
    document = load_example("runs/system-b.json")
    document["samples"].append(document["samples"][0].copy())
    document["samples"][0]["status"] = "failed"
    document["samples"][0]["reason"] = "synthetic failure"
    document["failures_included"] = False
    messages = _messages(document)
    assert any("must be unique" in message for message in messages)
    assert any("must be true" in message for message in messages)


@pytest.mark.parametrize(
    ("release_class", "exposed", "registry", "failures", "rights", "fragment"),
    [
        ("demonstration", False, "community", True, "not_applicable", "marked exposed"),
        ("blind", True, "community", True, "not_applicable", "cannot be exposed"),
        ("demonstration", True, "official", False, "not_applicable", "include failures"),
        ("demonstration", True, "official", True, "unknown", "unknown media rights"),
    ],
)
def test_release_semantics(
    load_example,
    release_class: str,
    exposed: bool,
    registry: str,
    failures: bool,
    rights: str,
    fragment: str,
) -> None:
    document = load_example("evidence-release.json")
    document.update(
        release_class=release_class,
        exposed_before_freeze=exposed,
        registry=registry,
        failures_included=failures,
        media_license_status=rights,
    )
    assert any(fragment in message for message in _messages(document))


def test_adaptation_disjoint_metrics_and_decision_authority(load_example) -> None:
    document = load_example("owner-adaptation.json")
    document["heldout_sample_ids"] = [document["training_sample_ids"][0]]
    document["owner_metric_after"]["name"] = "other"
    document.pop("decision_authority")
    messages = _messages(document)
    assert any("disjoint" in message for message in messages)
    assert any("owner_metric_before" in message for message in messages)
    assert any("decision_authority" in message for message in messages)


def test_recipe_digest_and_order_are_checked(load_example) -> None:
    document = load_example("evidence-recipe.json")
    assert document["recipe_digest"]["value"] == canonical_recipe_digest(document)
    document["items"][0]["order"] = 1
    document["recipe_digest"]["value"] = "0" * 64
    messages = _messages(document)
    assert any("contiguous" in message for message in messages)
    assert any("canonical recipe digest" in message for message in messages)


def test_agent_receipt_cannot_invent_extra_matches(load_example) -> None:
    document = load_example("coach-agent-run-receipt.json")
    document["available_match_count"] = 6
    assert any("cannot exceed requested" in message for message in _messages(document))


def test_model_observation_requires_identity_and_confidence(load_example) -> None:
    document = load_example("rallies/prediction.json")
    document["rallies"][0]["provenance"].pop("model_id")
    document["rallies"][0]["provenance"].pop("confidence")
    messages = _messages(document)
    assert any("requires model_id" in message for message in messages)
    assert any("requires confidence" in message for message in messages)


@pytest.mark.parametrize(
    "value",
    [
        {"token": "redacted"},
        "-----BEGIN PRIVATE KEY-----",
        "ghp_abcdefghijklmnopqrstuvwxyz",
        "AKIAABCDEFGHIJKLMNOP",
        "/home/person/private/file",
        r"C:\Users\person\Documents\file",
        "internal.example.ts.net",
        "http://localhost:8000",
        "http://192.168.1.2",
        "http://172.16.8.9",
    ],
)
def test_public_safety_scan_rejects_private_shapes(value: object) -> None:
    assert safety_issues(value)


def test_validate_path_reports_invalid_document(tmp_path: Path, load_example) -> None:
    path = tmp_path / "bad.json"
    document = load_example("scenario-profile.json")
    document["visible_courts"] = 0
    path.write_text(json.dumps(document), encoding="utf-8")
    assert str(path) in validate_path(tmp_path)
