import hashlib
import json
from pathlib import Path

import pytest

from khelsutra_evidence.cli import main
from khelsutra_evidence.disclosure import DisclosureControls, scan_disclosures


def test_disclosure_controls_are_independent_and_do_not_echo_content(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("Qwen3.5-9B R64 LoRA\nhttps://private.tail123.ts.net/repo\n")
    findings = scan_disclosures(tmp_path, DisclosureControls())
    assert {f["reason"] for f in findings} == {
        "model_or_training_recipe",
        "private_service_reference",
    }
    assert "Qwen" not in json.dumps(findings)
    assert scan_disclosures(tmp_path, DisclosureControls(enabled=False)) == []
    assert scan_disclosures(tmp_path, DisclosureControls(mode="off")) == []
    assert {f["reason"] for f in scan_disclosures(tmp_path, DisclosureControls(recipes=False))} == {
        "private_service_reference"
    }
    assert {
        f["reason"]
        for f in scan_disclosures(tmp_path, DisclosureControls(private_references=False))
    } == {"model_or_training_recipe"}


def test_exact_review_digest_does_not_approve_later_edits(tmp_path: Path) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(b"synthetic model bytes")
    controls = DisclosureControls(reviewed_sha256=(hashlib.sha256(path.read_bytes()).hexdigest(),))
    assert scan_disclosures(tmp_path, controls) == []
    path.write_bytes(b"different synthetic bytes")
    assert scan_disclosures(tmp_path, controls)[0]["reason"] == "model_asset"
    assert scan_disclosures(tmp_path, DisclosureControls(model_assets=False)) == []


@pytest.mark.parametrize(
    "value",
    [
        {"enabled": False, "recipes": "false"},
        {"mode": "typo"},
        {"unknown": True},
        {"reviewed_sha256": ["bad"]},
        {"reviewed_sha256": "bad"},
    ],
)
def test_invalid_controls_fail_even_when_master_disabled(value: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        DisclosureControls.parse(value)


def test_parse_valid_controls() -> None:
    assert DisclosureControls.parse({"mode": "enforce", "recipes": False}).recipes is False


def test_unreviewable_inputs_and_missing_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        scan_disclosures(tmp_path / "missing", DisclosureControls())
    (tmp_path / "binary.txt").write_bytes(b"\xff")
    (tmp_path / "large.txt").write_bytes(b"x" * ((4 << 20) + 1))
    (tmp_path / "link.md").symlink_to(tmp_path / "binary.txt")
    assert {f["reason"] for f in scan_disclosures(tmp_path, DisclosureControls())} == {
        "non_utf8_not_reviewed",
        "oversized_file_not_reviewed",
        "symlink_not_reviewed",
    }


def test_cli_observe_enforce_and_no_implicit_historical_approval(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    note = tmp_path / "note.md"
    note.write_text("666 training windows")
    assert main(["disclosure-review", str(note)]) == 0
    assert json.loads(capsys.readouterr().out)["findings"]
    controls = tmp_path / "controls.json"
    controls.write_text('{"mode":"enforce"}')
    assert main(["disclosure-review", str(note), "--controls", str(controls)]) == 1


def test_sampling_settings_and_explicit_publication_directory(tmp_path: Path) -> None:
    generated = tmp_path / "dist"
    generated.mkdir()
    note = generated / "note.md"
    note.write_text("Synthetic pipeline: 2 fps with JPEG quality 90\n")
    assert scan_disclosures(tmp_path, DisclosureControls()) == []
    assert scan_disclosures(generated, DisclosureControls()) == [
        {"path": "note.md", "line": 1, "reason": "model_or_training_recipe"}
    ]
    assert scan_disclosures(note, DisclosureControls(recipes=False)) == []
    (tmp_path / "source.py").write_text("666 training windows")
    (tmp_path / "folder.md").mkdir()
    assert scan_disclosures(tmp_path, DisclosureControls()) == []


def test_cli_invalid_controls_and_disabled_missing_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    controls = tmp_path / "controls.json"
    controls.write_text('{"enabled":false,"recipes":"false"}')
    args = ["disclosure-review", str(tmp_path / "missing"), "--controls", str(controls)]
    assert main(args) == 2
    capsys.readouterr()
    controls.write_text('{"enabled":false}')
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["findings"] == []
