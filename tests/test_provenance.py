"""How a run's output was produced is part of what its number means.

A model's score and a person's score are different claims. Putting them on one axis is often the
interesting comparison; doing it without saying so is the failure these tests guard.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from khelsutra_evidence.comparison import collect_provenance, compare_runs
from khelsutra_evidence.packaging import package_directory
from khelsutra_evidence.validation import validate_document


@pytest.fixture
def automated(load_example) -> dict[str, Any]:
    document: dict[str, Any] = load_example("system-provenance.json")
    return document


@pytest.fixture
def human(load_example) -> dict[str, Any]:
    document: dict[str, Any] = load_example("system-provenance.json")
    document["record_id"] = "system-provenance-synthetic-b"
    document["run_id"] = "synthetic-run-b"
    document["operation_mode"] = "human_produced"
    document["disclosure_basis"] = "observed"
    document["human_minutes_per_source_hour"] = 150
    return document


def _reasons(left, right, provenance=None) -> list[str]:
    report = compare_runs(left, right, provenance)
    return [str(reason) for reason in report["reasons"]]


def test_the_synthetic_disclosure_validates(automated) -> None:
    assert validate_document(automated) == []


def test_a_human_mode_must_say_how_much_human_time(automated) -> None:
    automated["operation_mode"] = "human_produced"
    automated.pop("human_minutes_per_source_hour")

    messages = [issue.render() for issue in validate_document(automated)]

    assert any("is the comparable fact" in message for message in messages)


def test_automated_cannot_bill_human_minutes(automated) -> None:
    automated["human_minutes_per_source_hour"] = 90

    messages = [issue.render() for issue in validate_document(automated)]

    assert any("must be zero or absent" in message for message in messages)


def test_undisclosed_mode_cannot_claim_a_basis(automated) -> None:
    automated["operation_mode"] = "undisclosed"

    messages = [issue.render() for issue in validate_document(automated)]

    assert any("must be 'unknown'" in message for message in messages)


@pytest.mark.parametrize("basis", ["vendor_stated", "observed"])
def test_a_stated_or_observed_disclosure_must_bind_its_receipt(automated, basis: str) -> None:
    automated["disclosure_basis"] = basis
    automated.pop("evidence_refs")

    messages = [issue.render() for issue in validate_document(automated)]

    assert any("must bind the document or observation" in message for message in messages)


def test_inferred_disclosure_needs_no_receipt(automated) -> None:
    automated["disclosure_basis"] = "inferred"
    automated.pop("evidence_refs")

    assert validate_document(automated) == []


def test_undeclared_runs_are_reported_as_undisclosed(load_example) -> None:
    reasons = _reasons(load_example("runs/system-a.json"), load_example("runs/system-b.json"))

    assert any("undisclosed for both runs" in reason for reason in reasons)


def test_one_declared_side_names_which_side_is_missing(load_example, automated) -> None:
    reasons = _reasons(
        load_example("runs/system-a.json"),
        load_example("runs/system-b.json"),
        {"synthetic-run-a": automated},
    )

    assert any("undisclosed for the right run" in reason for reason in reasons)


def test_a_model_against_a_person_is_stated_not_hidden(load_example, automated, human) -> None:
    reasons = _reasons(
        load_example("runs/system-a.json"),
        load_example("runs/system-b.json"),
        {"synthetic-run-a": automated, "synthetic-run-b": human},
    )

    assert any(
        "operation mode differs: automated versus human-produced" in reason for reason in reasons
    )


def test_matching_modes_are_stated_too(load_example, automated) -> None:
    right = dict(automated, record_id="p-b", run_id="synthetic-run-b")

    reasons = _reasons(
        load_example("runs/system-a.json"),
        load_example("runs/system-b.json"),
        {"synthetic-run-a": automated, "synthetic-run-b": right},
    )

    assert any("both runs are automated" in reason for reason in reasons)


def test_provenance_does_not_move_the_verdict(load_example, automated, human) -> None:
    left = load_example("runs/system-a.json")
    right = load_example("runs/system-b.json")

    without = compare_runs(left, right)["verdict"]
    with_it = compare_runs(left, right, {"synthetic-run-a": automated, "synthetic-run-b": human})[
        "verdict"
    ]

    assert without == with_it == "paired_quality_only"


def test_the_report_still_satisfies_its_own_contract(load_example, automated, human) -> None:
    report = compare_runs(
        load_example("runs/system-a.json"),
        load_example("runs/system-b.json"),
        {"synthetic-run-a": automated, "synthetic-run-b": human},
    )

    assert validate_document(report) == []


def test_collect_keys_by_run_and_ignores_other_documents(automated, load_example) -> None:
    collected = collect_provenance(
        [("a.json", automated), ("b.json", load_example("task-profile.json"))]
    )

    assert list(collected) == ["synthetic-run-a"]


def test_collect_refuses_an_invalid_disclosure(automated) -> None:
    automated["operation_mode"] = "human_produced"
    automated.pop("human_minutes_per_source_hour")

    with pytest.raises(ValueError, match="invalid system provenance"):
        collect_provenance([("a.json", automated)])


@pytest.mark.parametrize("basis", ["observed", "inferred", "unknown"])
def test_a_conclusion_about_another_system_is_not_publishable(
    automated, tmp_path: Path, basis: str
) -> None:
    # Repeating what a vendor stated is publishable. Concluding it yourself is a competitive claim,
    # and this repository is not where competitive claims live.
    automated["disclosure_basis"] = basis
    if basis == "unknown":
        automated["operation_mode"] = "undisclosed"
    source = tmp_path / "source"
    source.mkdir()
    (source / "provenance.json").write_text(json.dumps(automated), encoding="utf-8")

    with pytest.raises(ValueError, match="competitive claim"):
        package_directory(source, tmp_path / "out.tar.gz")


def test_a_vendor_stated_disclosure_may_be_published(automated, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "provenance.json").write_text(json.dumps(automated), encoding="utf-8")

    assert len(package_directory(source, tmp_path / "out.tar.gz")) == 64
