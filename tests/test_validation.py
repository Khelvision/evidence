from __future__ import annotations

import json
from pathlib import Path

import pytest

from khelsutra_evidence.schemas import load_schemas, schemas_by_name, validator_for
from khelsutra_evidence.validation import (
    canonical_plan_digest,
    canonical_recipe_digest,
    json_paths,
    load_json,
    safety_issues,
    validate_document,
    validate_json_document,
    validate_path,
)


def _synthetic_secret(prefix: str, body: str) -> str:
    """Assemble a secret-shaped test value at run time.

    The scanner must see the whole value, but committing the whole literal makes the push mirror to
    the GitHub backup fail GitHub push protection, so the halves are stored apart and joined here.
    """
    return prefix + body


def _messages(document: dict[str, object]) -> list[str]:
    return [issue.render() for issue in validate_document(document)]


def test_all_synthetic_examples_validate(examples_root: Path) -> None:
    assert validate_path(examples_root) == {}
    assert len(schemas_by_name()) == 21
    assert len(load_schemas()) == 22


def test_public_registries_and_schema_documents_validate() -> None:
    root = Path(__file__).resolve().parents[1]
    assert validate_path(root / "registry") == {}
    assert validate_path(root / "schemas" / "v1") == {}


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


def test_json_schema_documents_require_draft_and_identifier() -> None:
    messages = [issue.render() for issue in validate_json_document({"$schema": "other"})]
    assert any("Draft 2020-12" in message for message in messages)
    assert any("identifier" in message for message in messages)
    invalid_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:khelsutra:evidence:schema:v1:InvalidTestSchema",
        "type": "not-a-json-schema-type",
    }
    assert any(
        "invalid JSON Schema" in issue.render() for issue in validate_json_document(invalid_schema)
    )
    schema_with_ref_literal = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:khelsutra:evidence:schema:v1:RefLiteralTestSchema",
        "type": "object",
        "examples": [{"$ref": "this-is-instance-data-not-a-schema-reference"}],
    }
    assert validate_json_document(schema_with_ref_literal) == []


def test_json_schema_documents_reject_unresolvable_references() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "schemas/v1/cost-receipt.json").read_text(encoding="utf-8"))
    schema["properties"]["record_id"]["$ref"] = (
        "urn:khelsutra:evidence:schema:v1:commonX#/$defs/recordId"
    )

    issues = validate_json_document(schema)

    assert [issue.path for issue in issues] == ["properties.record_id.$ref"]
    assert "unresolvable JSON Schema reference" in issues[0].message


def test_json_paths_ignore_tool_environments_but_not_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}", encoding="utf-8")
    tool_file = tmp_path / ".venv-ci" / "metadata.json"
    tool_file.parent.mkdir()
    tool_file.write_text("{}", encoding="utf-8")

    assert json_paths(tmp_path) == [evidence]


def test_scenario_active_games_cannot_exceed_visible(load_example) -> None:
    document = load_example("scenario-profile.json")
    document["simultaneously_active_games"] = 4
    assert any("cannot exceed" in message for message in _messages(document))


def test_commercialization_overall_is_derived(load_example) -> None:
    document = load_example("commercialization-readiness.json")
    document["overall_status"] = "verified_clear"
    assert any("must be 'restricted'" in message for message in _messages(document))


def test_commercialization_requires_each_unique_rights_category(load_example) -> None:
    document = load_example("commercialization-readiness.json")
    document["components"][-1] = document["components"][0].copy()
    messages = _messages(document)
    assert any("categories must be unique" in message for message in messages)
    assert any("missing commercialization categories" in message for message in messages)


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


def test_rallies_on_different_courts_may_overlap(load_example) -> None:
    document = load_example("rallies/truth.json")
    document["rallies"][1].update(
        target_court_id="court-b",
        start_frame=150,
        end_frame=200,
    )
    assert not any("must not overlap" in message for message in _messages(document))


def test_rally_issue_paths_use_submitted_document_indices(load_example) -> None:
    document = load_example("rallies/truth.json")
    document["rallies"] = [
        {
            **document["rallies"][0],
            "rally_id": "rally-court-2",
            "target_court_id": "court-2",
            "start_frame": 10,
            "end_frame": 20,
        },
        {
            **document["rallies"][0],
            "rally_id": "rally-court-1-first",
            "target_court_id": "court-1",
            "start_frame": 100,
            "end_frame": 200,
        },
        {
            **document["rallies"][0],
            "rally_id": "rally-court-1-overlap",
            "target_court_id": "court-1",
            "start_frame": 150,
            "end_frame": 260,
        },
    ]

    messages = _messages(document)

    assert "rallies.2: rallies must not overlap" in messages
    assert "rallies.1: rallies must not overlap" not in messages


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


def test_plan_digest_permissions_and_ambiguity_are_checked(load_example) -> None:
    document = load_example("coach-instruction-plan.json")
    assert document["plan_digest"]["value"] == canonical_plan_digest(document)
    document["ambiguities"] = ["Player A resolves to two people."]
    document["permission_checks"][0].pop("grant_ref")
    document["plan_digest"]["value"] = "0" * 64
    messages = _messages(document)
    assert any("canonical plan digest" in message for message in messages)
    assert any("require clarification" in message for message in messages)
    assert any("required when a permission is granted" in message for message in messages)


def test_plan_rejects_clarification_without_ambiguity(load_example) -> None:
    document = load_example("coach-instruction-plan.json")
    document["execution_status"] = "requires_clarification"
    assert any("cannot require clarification" in message for message in _messages(document))


def test_plan_requires_unique_permission_purposes(load_example) -> None:
    document = load_example("coach-instruction-plan.json")
    document["permission_checks"].append(document["permission_checks"][0].copy())
    assert any("purposes must be unique" in message for message in _messages(document))


def test_ready_plan_requires_service_operation_grant(load_example) -> None:
    document = load_example("coach-instruction-plan.json")
    document["permission_checks"][0] = {
        "purpose": "service_operation",
        "granted": False,
    }
    assert any("requires a granted service_operation" in message for message in _messages(document))


def test_portability_requires_clean_second_environment_and_receipts(load_example) -> None:
    document = load_example("ownership-portability.json")
    document.pop("second_environment")
    document["restore"]["artifact_refs"] = []
    messages = _messages(document)
    assert any("second_environment" in message for message in messages)
    assert any("artifact_refs" in message for message in messages)


def test_agent_receipt_cannot_invent_extra_matches(load_example) -> None:
    document = load_example("coach-agent-run-receipt.json")
    document["available_match_count"] = 6
    assert any("cannot exceed requested" in message for message in _messages(document))


def test_agent_receipt_explains_incomplete_scope_and_binds_artifacts(load_example) -> None:
    document = load_example("coach-agent-run-receipt.json")
    document["omissions"] = []
    document["result_artifacts"] = []
    messages = _messages(document)
    assert any("fewer than the requested" in message for message in messages)
    assert any("listed in result_artifacts" in message for message in messages)


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
        {"checkpoint_path": "/private/model"},
        {_synthetic_secret("ghp_", "abcdefghijklmnopqrstuvwxyz"): "redacted"},
        "-----BEGIN PRIVATE KEY-----",
        _synthetic_secret("ghp_", "abcdefghijklmnopqrstuvwxyz"),
        _synthetic_secret("AIza", "abcdefghijklmnopqrstuvwxyz123456789"),
        _synthetic_secret("xoxb-", "1234567890-abcdefghijklmnopqrstuvwxyz"),
        _synthetic_secret("eyJ", "abcdefghijk.abcdefghijkl.abcdefghijkl"),
        "https://example.invalid/object?X-Amz-Signature=not-public",
        _synthetic_secret("AKIA", "ABCDEFGHIJKLMNOP"),
        "/home/person/private/file",
        "[private file](/home/person/private/file)",
        "file:///home/person/private/file",
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


def test_validate_path_reports_unrecognized_json(tmp_path: Path) -> None:
    path = tmp_path / "unrecognized.json"
    path.write_text(json.dumps({"schema_Name": "TaskProfileV1"}), encoding="utf-8")

    failures = validate_path(tmp_path)

    assert str(path) in failures
    assert failures[str(path)][0].render() == "schema_name: missing string schema_name"
