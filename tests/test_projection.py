from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from khelsutra_evidence.projection import (
    canonical_public_bytes,
    project_record,
    projection_refusals,
    public_record_digest,
)
from khelsutra_evidence.validation import validate_document

REFUSING_FIXTURES = [
    ("public-schema-drift.json", "public_schema_drift", "internal_confidence"),
    ("unsafe-public-value.json", "unsafe_public_value", "private IPv4 endpoint"),
    ("unauthorized-media-grant.json", "unauthorized_media", "not 'verified_clear'"),
    ("unlisted-media.json", "unauthorized_media", "no media authorization"),
    ("media-without-public-purpose.json", "unauthorized_media", "public_evidence purpose"),
    ("dead-media-authorization.json", "dead_media_authorization", "never references"),
    ("private-value-echo.json", "private_value_echo", "private_extensions value"),
    ("projection-digest-mismatch.json", "projection_digest_mismatch", "canonical public record"),
]


def test_synthetic_private_record_projects_to_its_declared_digest(load_example) -> None:
    record = load_example("private-evidence-record.json")

    assert projection_refusals(record) == []
    payload = project_record(record)

    declared = record["projection"]["public_record_digest"]["value"]
    assert hashlib.sha256(payload).hexdigest() == declared
    assert public_record_digest(record["public"]) == declared
    assert json.loads(payload) == record["public"]


def test_projection_bytes_are_canonical_and_stable(load_example) -> None:
    record = load_example("private-evidence-record.json")
    reordered = load_example("private-evidence-record.json")
    reordered["public"] = dict(reversed(list(reordered["public"].items())))

    assert project_record(record) == project_record(reordered)
    assert b"\n" not in canonical_public_bytes(record["public"])


@pytest.mark.parametrize(("filename", "reason", "fragment"), REFUSING_FIXTURES)
def test_negative_fixture_is_refused_for_exactly_one_reason(
    load_fixture, filename: str, reason: str, fragment: str
) -> None:
    refusals = projection_refusals(load_fixture(f"projection/{filename}"))

    assert {refusal.reason for refusal in refusals} == {reason}
    assert any(fragment in refusal.render() for refusal in refusals)


def test_every_negative_fixture_remains_a_valid_private_record(fixtures_root: Path) -> None:
    for path in sorted((fixtures_root / "projection").glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        assert validate_document(document) == [], path


def test_negative_fixture_inventory_is_complete(fixtures_root: Path) -> None:
    present = {path.name for path in (fixtures_root / "projection").glob("*.json")}
    assert present == {filename for filename, _, _ in REFUSING_FIXTURES}


def test_projection_input_must_be_a_private_record(load_example) -> None:
    refusals = projection_refusals(load_example("coach-agent-run-receipt.json"))

    assert [refusal.reason for refusal in refusals] == ["envelope_invalid"]
    assert "PrivateEvidenceRecordV1" in refusals[0].message


def test_unclassified_top_level_material_is_refused(load_example) -> None:
    record = load_example("private-evidence-record.json")
    record["operator_scratchpad"] = "unclassified"

    refusals = projection_refusals(record)

    assert [refusal.reason for refusal in refusals] == ["envelope_invalid"]
    assert "Additional properties" in refusals[0].message


def test_private_record_cannot_publish_itself(load_example) -> None:
    record = load_example("private-evidence-record.json")
    record["public"] = load_example("private-evidence-record.json")

    refusals = projection_refusals(record)

    assert any(refusal.reason == "public_schema_drift" for refusal in refusals)
    assert any("cannot be published" in refusal.message for refusal in refusals)


def test_media_authorizations_must_name_distinct_artifacts(load_example) -> None:
    record = load_example("private-evidence-record.json")
    record["media_authorizations"].append(
        record["media_authorizations"][0] | {"custody": "third_party"}
    )

    messages = [issue.render() for issue in validate_document(record)]

    assert any("artifact_id values must be unique" in message for message in messages)


def test_public_payload_must_name_a_published_contract(load_example) -> None:
    record = load_example("private-evidence-record.json")
    record["public"] = {"schema_name": "NotAContractV1"}

    messages = [issue.render() for issue in validate_document(record)]

    assert any("published public evidence contract" in message for message in messages)


def test_project_record_raises_with_every_refusal(load_fixture) -> None:
    record = load_fixture("projection/unlisted-media.json")
    record["projection"]["public_record_digest"]["value"] = "0" * 64

    with pytest.raises(ValueError) as excinfo:
        project_record(record)

    assert "publication refused" in str(excinfo.value)
    assert "unauthorized_media" in str(excinfo.value)
    assert "projection_digest_mismatch" in str(excinfo.value)


def test_records_without_private_extensions_skip_the_echo_scan(load_example) -> None:
    record = load_example("private-evidence-record.json")
    record["private_extensions"] = {}
    record["projection"]["public_record_digest"]["value"] = public_record_digest(record["public"])

    assert projection_refusals(record) == []
