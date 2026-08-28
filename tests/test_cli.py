from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from khelsutra_evidence import schemas as schema_module
from khelsutra_evidence.cli import main


def _json_output(capsys) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def test_init_and_verify(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", str(workspace)]) == 0
    assert _json_output(capsys)["status"] == "created"
    assert main(["verify", str(workspace)]) == 0
    output = _json_output(capsys)
    assert output == {"documents": 2, "status": "valid"}


def test_init_existing_path_returns_error(tmp_path: Path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 2
    error = json.loads(capsys.readouterr().err)
    assert error["status"] == "error"


def test_verify_invalid_and_empty(tmp_path: Path, capsys, load_example) -> None:
    bad = load_example("scenario-profile.json")
    bad["visible_courts"] = 0
    (tmp_path / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
    assert main(["verify", str(tmp_path)]) == 1
    assert _json_output(capsys)["status"] == "invalid"
    (tmp_path / "bad.json").unlink()
    (tmp_path / "unrecognized.json").write_text(
        json.dumps({"schema_Name": "ScenarioProfileV1"}), encoding="utf-8"
    )
    assert main(["verify", str(tmp_path)]) == 1
    error = _json_output(capsys)
    assert error["status"] == "invalid"
    assert "missing string schema_name" in error["files"][str(tmp_path / "unrecognized.json")][0]
    (tmp_path / "unrecognized.json").unlink()
    assert main(["verify", str(tmp_path)]) == 2
    error = json.loads(capsys.readouterr().err)
    assert "no JSON documents" in error["message"]


def test_verify_schema_resolution_failure_is_structured_error(
    tmp_path: Path, capsys, load_example, monkeypatch
) -> None:
    schemas = deepcopy(schema_module.load_schemas())
    cost_id = "urn:khelsutra:evidence:schema:v1:CostReceiptV1"
    schemas[cost_id]["properties"]["record_id"]["$ref"] = (
        "urn:khelsutra:evidence:schema:v1:commonX#/$defs/recordId"
    )
    monkeypatch.setattr(schema_module, "load_schemas", lambda: schemas)
    schema_module.schema_registry.cache_clear()
    schema_module.schemas_by_name.cache_clear()
    path = tmp_path / "cost.json"
    path.write_text(json.dumps(load_example("cost-receipt.json")), encoding="utf-8")

    try:
        assert main(["verify", str(path)]) == 2
    finally:
        schema_module.schema_registry.cache_clear()
        schema_module.schemas_by_name.cache_clear()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "message": "Unresolvable: urn:khelsutra:evidence:schema:v1:commonX#/$defs/recordId",
        "status": "error",
    }


def test_score_compare_and_package_commands(examples_root: Path, tmp_path: Path, capsys) -> None:
    score_path = tmp_path / "score.json"
    assert (
        main(
            [
                "score",
                str(examples_root / "rallies/truth.json"),
                str(examples_root / "rallies/prediction.json"),
                "--output",
                str(score_path),
            ]
        )
        == 0
    )
    assert json.loads(score_path.read_text(encoding="utf-8"))["matched_count"] == 2
    compare_path = tmp_path / "compare.json"
    assert (
        main(
            [
                "compare",
                str(examples_root / "runs/system-a.json"),
                str(examples_root / "runs/system-b.json"),
                "--output",
                str(compare_path),
            ]
        )
        == 0
    )
    assert json.loads(compare_path.read_text(encoding="utf-8"))["verdict"] == "paired_quality_only"
    archive = tmp_path / "examples.tar.gz"
    assert main(["package", str(examples_root), str(archive)]) == 0
    assert _json_output(capsys)["status"] == "packaged"
    assert archive.exists()


def test_score_prints_result_and_bad_json_is_reported(
    examples_root: Path, tmp_path: Path, capsys
) -> None:
    assert (
        main(
            [
                "score",
                str(examples_root / "rallies/truth.json"),
                str(examples_root / "rallies/prediction.json"),
            ]
        )
        == 0
    )
    assert _json_output(capsys)["schema_name"] == "RallyScoreV1"
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert main(["verify", str(bad)]) == 2
    assert json.loads(capsys.readouterr().err)["status"] == "error"


def test_project_writes_the_declared_public_record(
    private_examples_root: Path, tmp_path: Path, capsysbinary
) -> None:
    record_path = private_examples_root / "private-evidence-record.json"
    declared = json.loads(record_path.read_text(encoding="utf-8"))["projection"][
        "public_record_digest"
    ]["value"]

    assert main(["project", str(record_path)]) == 0
    streamed = capsysbinary.readouterr().out
    assert hashlib.sha256(streamed).hexdigest() == declared

    output = tmp_path / "published" / "public.json"
    assert main(["project", str(record_path), "--output", str(output)]) == 0
    assert hashlib.sha256(output.read_bytes()).hexdigest() == declared
    assert streamed == output.read_bytes()


def test_project_refuses_on_stderr_without_emitting_a_record(fixtures_root: Path, capsys) -> None:
    fixture = fixtures_root / "projection" / "unauthorized-media-grant.json"

    assert main(["project", str(fixture)]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    refusal = json.loads(captured.err)
    assert refusal["status"] == "refused"
    assert [entry["reason"] for entry in refusal["refusals"]] == ["unauthorized_media"]


def test_media_preflight_clears_a_granted_release(tmp_path: Path, capsys, load_example) -> None:
    grants = tmp_path / "grants"
    grants.mkdir()
    (grants / "sample-001.json").write_text(
        json.dumps(load_example("media-grant.json")), encoding="utf-8"
    )
    release = load_example("evidence-release.json")
    release_path = tmp_path / "release.json"
    release_path.write_text(json.dumps(release), encoding="utf-8")

    assert main(["media-preflight", str(release_path), str(grants)]) == 0

    report = _json_output(capsys)
    assert report["summary"] == {"requested": 1, "cleared": 1, "blocked": 0}


def test_media_preflight_exits_nonzero_when_a_sample_is_not_cleared(
    tmp_path: Path, capsys, load_example
) -> None:
    grants = tmp_path / "grants"
    grants.mkdir()
    (grants / "unrelated.json").write_text(
        json.dumps(load_example("task-profile.json")), encoding="utf-8"
    )
    release = load_example("evidence-release.json")
    release_path = tmp_path / "release.json"
    release_path.write_text(json.dumps(release), encoding="utf-8")

    assert main(["media-preflight", str(release_path), str(grants)]) == 1

    report = _json_output(capsys)
    assert report["samples"][0]["gaps"][0]["requirement"] == "no_grant"


def test_media_preflight_accepts_an_owner_attestation(
    tmp_path: Path, capsys, load_example, examples_root: Path
) -> None:
    grants = tmp_path / "grants"
    grants.mkdir()
    release_path = tmp_path / "release.json"
    release_path.write_text(json.dumps(load_example("evidence-release.json")), encoding="utf-8")

    assert (
        main(
            [
                "media-preflight",
                str(release_path),
                str(grants),
                "--rights-basis",
                str(examples_root / "release-rights-basis.json"),
            ]
        )
        == 0
    )

    report = _json_output(capsys)
    assert report["rights_basis"] == "owner_attestation"
    assert report["summary"]["blocked"] == 0


def test_parser_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        main([])
