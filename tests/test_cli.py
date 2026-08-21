from __future__ import annotations

import json
from pathlib import Path

import pytest

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
    assert main(["verify", str(tmp_path)]) == 2
    error = json.loads(capsys.readouterr().err)
    assert "no schema documents" in error["message"]


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


def test_parser_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        main([])
