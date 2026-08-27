"""Replay the portable conformance suite through the public API.

These tests consume `conformance/v1/manifest.json` the way a foreign implementation would: by
reading the corpus and running each case against the public entry points. They deliberately do not
reuse the renderer's helpers, so a renderer bug cannot make the corpus agree with itself.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from khelsutra_evidence.comparison import compare_runs
from khelsutra_evidence.packaging import archive_members, package_directory
from khelsutra_evidence.projection import projection_refusals, public_record_digest
from khelsutra_evidence.scoring import score_rallies
from khelsutra_evidence.validation import (
    canonical_plan_digest,
    canonical_recipe_digest,
    canonical_suite_digest,
    safety_issues,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "conformance" / "v1" / "manifest.json"
OPERATIONS = {
    "validate_document",
    "score_rallies",
    "compare_runs",
    "plan_digest",
    "recipe_digest",
    "public_safety",
    "project_record",
    "package_archive",
}


@pytest.fixture(scope="module")
def suite() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return loaded


def _renderer() -> Any:
    spec = importlib.util.spec_from_file_location(
        "render_conformance", ROOT / "tools" / "render_conformance.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _case_ids(suite: dict[str, Any]) -> list[str]:
    return [str(case["case_id"]) for case in suite["cases"]]


def test_checked_in_suite_matches_the_renderer() -> None:
    assert MANIFEST.read_text(encoding="utf-8") == _renderer().render()


def test_suite_is_self_describing(suite: dict[str, Any]) -> None:
    assert suite["schema_name"] == "ConformanceSuiteV1"
    assert suite["contract_version"] == "v1"
    assert validate_document(suite) == []
    assert suite["suite_digest"]["value"] == canonical_suite_digest(suite)
    assert _case_ids(suite) == sorted(_case_ids(suite))


def test_every_operation_is_exercised(suite: dict[str, Any]) -> None:
    assert {str(case["operation"]) for case in suite["cases"]} == OPERATIONS


def _replay(case: dict[str, Any]) -> dict[str, Any]:
    operation = case["operation"]
    given = case["input"]

    if operation == "validate_document":
        issues = validate_document(given["document"])
        return {
            "valid": not issues,
            "issue_paths": sorted({issue.path for issue in issues}),
            "messages": [issue.render() for issue in issues],
        }
    if operation == "score_rallies":
        return _guard(
            lambda: score_rallies(given["truth"], given["prediction"], given["tolerance_frames"])
        )
    if operation == "compare_runs":
        return _guard(lambda: compare_runs(given["left"], given["right"]))
    if operation in {"plan_digest", "recipe_digest"}:
        compute = canonical_plan_digest if operation == "plan_digest" else canonical_recipe_digest
        return {"digest": compute(given["document"])}
    if operation == "public_safety":
        return {"issues": [issue.render() for issue in safety_issues(given["value"])]}
    if operation == "project_record":
        refusals = projection_refusals(given["record"])
        replayed: dict[str, Any] = {
            "refusals": [
                {"reason": item.reason, "path": item.path, "message": item.message}
                for item in refusals
            ]
        }
        if not refusals:
            replayed["public_record_digest"] = public_record_digest(given["record"]["public"])
        return replayed
    assert operation == "package_archive"
    return _replay_package(given["files"])


def _guard(call: Any) -> dict[str, Any]:
    try:
        return {"result": call()}
    except ValueError as exc:
        return {"error": str(exc)}


def _replay_package(files: list[dict[str, Any]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as raw:
        source = Path(raw) / "source"
        source.mkdir()
        for entry in files:
            (source / str(entry["name"])).write_text(str(entry["text"]), encoding="utf-8")
        destination = Path(raw) / "archive.tar.gz"
        try:
            sha256 = package_directory(source, destination)
        except ValueError as exc:
            return {"error": str(exc).replace(f"{source}/", "")}
        return {"members": archive_members(destination), "sha256": sha256}


def test_reference_implementation_passes_every_case(suite: dict[str, Any]) -> None:
    failures: list[str] = []
    for case in suite["cases"]:
        replayed = _replay(case)
        expected = dict(case["expect"])
        if case["operation"] == "validate_document":
            # Schema-stage wording belongs to whichever JSON Schema library ran; only paths bind.
            if expected.pop("stage") == "schema":
                expected.pop("messages")
                replayed.pop("messages")
            else:
                expected.pop("stage", None)
        if replayed != expected:
            failures.append(f"{case['case_id']}: expected {expected!r}, replayed {replayed!r}")
    assert not failures, "\n".join(failures)


def test_schema_stage_cases_do_not_bind_library_wording(suite: dict[str, Any]) -> None:
    schema_stage = [
        case
        for case in suite["cases"]
        if case["operation"] == "validate_document" and case["expect"]["stage"] == "schema"
    ]
    assert schema_stage, "the corpus must show at least one schema-stage rejection"
    for case in schema_stage:
        assert case["expect"]["issue_paths"], case["case_id"]


def test_duplicate_case_ids_are_rejected(suite: dict[str, Any]) -> None:
    broken = json.loads(json.dumps(suite))
    broken["cases"].append(broken["cases"][0])
    broken["suite_digest"]["value"] = canonical_suite_digest(broken)

    messages = [issue.render() for issue in validate_document(broken)]

    assert any("case_id values must be unique" in message for message in messages)


def test_unordered_cases_are_rejected(suite: dict[str, Any]) -> None:
    broken = json.loads(json.dumps(suite))
    broken["cases"] = list(reversed(broken["cases"]))
    broken["suite_digest"]["value"] = canonical_suite_digest(broken)

    messages = [issue.render() for issue in validate_document(broken)]

    assert any("must be ordered by case_id" in message for message in messages)


def test_unbound_suite_digest_is_rejected(suite: dict[str, Any]) -> None:
    broken = json.loads(json.dumps(suite))
    broken["suite_digest"]["value"] = "0" * 64

    messages = [issue.render() for issue in validate_document(broken)]

    assert any("canonical suite digest" in message for message in messages)
