"""Media grants decide whether a release's footage may be published at all.

The grant fixtures each withhold exactly one thing, so a change that starts clearing one of them is
a change that starts publishing footage on a permission nobody gave.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from khelsutra_evidence.media import collect_grants, grant_gaps, preflight
from khelsutra_evidence.validation import validate_document

BLOCKING_FIXTURES = [
    ("publication-not-clear.json", "publication_not_verified_clear"),
    ("venue-unresolved.json", "venue_permission_unresolved"),
    ("no-participants.json", "no_participants_recorded"),
    ("consent-without-public-evidence.json", "participant_consent_missing_public_evidence"),
    ("guardian-authorization-missing.json", "guardian_authorization_missing"),
    ("participant-withdrawn.json", "participant_withdrawn"),
]


@pytest.fixture
def release(load_example):
    document: dict[str, Any] = load_example("evidence-release.json")
    return document


def test_a_fully_granted_sample_clears(load_example) -> None:
    grant = load_example("media-grant.json")

    assert validate_document(grant) == []
    assert grant_gaps(grant) == []


@pytest.mark.parametrize(("filename", "requirement"), BLOCKING_FIXTURES)
def test_each_fixture_withholds_exactly_one_thing(
    load_fixture, filename: str, requirement: str
) -> None:
    gaps = grant_gaps(load_fixture(f"media/{filename}"))

    assert {gap.requirement for gap in gaps} == {requirement}


def test_every_blocking_fixture_is_still_a_valid_grant(fixtures_root: Path) -> None:
    for path in sorted((fixtures_root / "media").glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        assert validate_document(document) == [], path


def test_blocking_fixture_inventory_is_complete(fixtures_root: Path) -> None:
    present = {path.name for path in (fixtures_root / "media").glob("*.json")}
    assert present == {filename for filename, _ in BLOCKING_FIXTURES}


def test_a_sample_with_no_grant_is_blocked(release, load_example) -> None:
    report = preflight(release, [])

    assert report["summary"] == {"requested": 1, "cleared": 0, "blocked": 1}
    assert report["samples"][0]["gaps"][0]["requirement"] == "no_grant"


def test_a_granted_release_clears_and_reports_what_it_permits(release, load_example) -> None:
    report = preflight(release, [load_example("media-grant.json")])

    assert report["summary"] == {"requested": 1, "cleared": 1, "blocked": 0}
    assert report["samples"][0]["cleared"] is True
    assert report["samples"][0]["permits"] == {
        "training": False,
        "rehosting": False,
        "custody": "owner_controlled",
    }


def test_clearing_publication_does_not_imply_training_or_rehosting(release, load_example) -> None:
    grant = load_example("media-grant.json")
    report = preflight(release, [grant])

    assert report["samples"][0]["cleared"] is True
    assert report["samples"][0]["permits"]["training"] is False
    assert report["samples"][0]["permits"]["rehosting"] is False


def test_partially_granted_release_reports_both_sides(release, load_example, load_fixture) -> None:
    release["sample_ids"] = ["synthetic-match-001", "synthetic-match-002"]
    blocked = load_fixture("media/venue-unresolved.json")
    blocked["sample_id"] = "synthetic-match-002"
    blocked["record_id"] = "media-grant-synthetic-match-002"

    report = preflight(release, [load_example("media-grant.json"), blocked])

    assert report["summary"] == {"requested": 2, "cleared": 1, "blocked": 1}
    assert [entry["cleared"] for entry in report["samples"]] == [True, False]


def test_grants_for_samples_outside_the_release_are_reported(release, load_example) -> None:
    other = load_example("media-grant.json")
    other["sample_id"] = "synthetic-match-999"
    other["record_id"] = "media-grant-synthetic-match-999"

    report = preflight(release, [load_example("media-grant.json"), other])

    assert report["unused_grants"] == ["synthetic-match-999"]


def test_duplicate_grants_for_one_sample_are_reported(release, load_example) -> None:
    report = preflight(release, [load_example("media-grant.json")] * 2)

    assert report["duplicate_grants"] == ["synthetic-match-001"]


def test_preflight_refuses_inputs_of_the_wrong_kind(release, load_example) -> None:
    with pytest.raises(ValueError, match="must use EvidenceReleaseV1"):
        preflight(load_example("media-grant.json"), [])
    with pytest.raises(ValueError, match="must use MediaGrantV1"):
        preflight(release, [load_example("evidence-release.json")])


def test_preflight_refuses_an_invalid_grant(release, load_example) -> None:
    broken = load_example("media-grant.json")
    broken["publication_grant"] = "sort-of-clear"

    with pytest.raises(ValueError, match="invalid media grant"):
        preflight(release, [broken])


def test_participant_handles_must_be_unique(load_example) -> None:
    grant = load_example("media-grant.json")
    grant["participants"][1]["participant_handle"] = "p1"

    messages = [issue.render() for issue in validate_document(grant)]

    assert any("participant_handle values must be unique" in message for message in messages)


def test_verified_clear_venue_must_name_its_grant(load_example) -> None:
    grant = load_example("media-grant.json")
    grant["venue_permission"] = {"state": "verified_clear"}

    messages = [issue.render() for issue in validate_document(grant)]

    assert any("must name its grant" in message for message in messages)


def test_guardian_reference_requires_the_flag(load_example) -> None:
    grant = load_example("media-grant.json")
    grant["participants"][0]["guardian_authorization_ref"] = grant["participants"][0]["consent_ref"]

    messages = [issue.render() for issue in validate_document(grant)]

    assert any("must be true when a guardian authorization" in message for message in messages)


def test_collect_grants_keeps_only_grants(load_example) -> None:
    documents = [
        ("a.json", load_example("media-grant.json")),
        ("b.json", load_example("evidence-release.json")),
        ("c.json", load_example("task-profile.json")),
    ]

    assert [grant["schema_name"] for grant in collect_grants(documents)] == ["MediaGrantV1"]


def test_gap_renders_for_a_human(load_fixture) -> None:
    gap = grant_gaps(load_fixture("media/venue-unresolved.json"))[0]

    assert gap.render() == (
        "synthetic-sample-001: venue_permission_unresolved: venue permission is 'unknown'"
    )
