from __future__ import annotations

import json
from pathlib import Path

import pytest

from khelsutra_evidence.packaging import archive_members, package_directory


def test_package_is_deterministic(tmp_path: Path, load_example) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "task.json").write_text(
        json.dumps(load_example("task-profile.json")), encoding="utf-8"
    )
    (source / "README.md").write_text("# Safe synthetic package\n", encoding="utf-8")
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    assert package_directory(source, first) == package_directory(source, second)
    assert first.read_bytes() == second.read_bytes()
    assert archive_members(first) == ["README.md", "task.json"]


def test_synthetic_example_package_has_stable_digest(examples_root: Path, tmp_path: Path) -> None:
    assert package_directory(examples_root, tmp_path / "examples.tar.gz") == (
        "f47253384c4596a06b7a41023f5f99a7eb60447accd388ae21f80a0f53a3a8e5"
    )


def test_package_rejects_empty_unsupported_large_or_symlink(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError, match="no supported files"):
        package_directory(source, tmp_path / "empty.tar.gz")
    (source / "bad.bin").write_bytes(b"bad")
    with pytest.raises(ValueError, match="unsupported"):
        package_directory(source, tmp_path / "bad.tar.gz")
    (source / "bad.bin").unlink()
    (source / "large.md").write_text("12345", encoding="utf-8")
    monkeypatch.setattr("khelsutra_evidence.packaging._MAX_FILE_BYTES", 4)
    with pytest.raises(ValueError, match="exceeds"):
        package_directory(source, tmp_path / "large.tar.gz")
    (source / "large.md").unlink()
    target = tmp_path / "target.md"
    target.write_text("safe", encoding="utf-8")
    (source / "link.md").symlink_to(target)
    with pytest.raises(ValueError, match="symbolic"):
        package_directory(source, tmp_path / "link.tar.gz")


def test_package_rejects_unsafe_or_invalid_json(tmp_path: Path, load_example) -> None:
    source = tmp_path / "source"
    source.mkdir()
    unsafe = load_example("task-profile.json")
    unsafe["token"] = "not-public"
    (source / "unsafe.json").write_text(json.dumps(unsafe), encoding="utf-8")
    with pytest.raises(ValueError, match="publication refused"):
        package_directory(source, tmp_path / "unsafe.tar.gz")
    (source / "unsafe.json").unlink()
    invalid = load_example("task-profile.json")
    invalid["sport"] = ""
    (source / "invalid.json").write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError, match="publication refused"):
        package_directory(source, tmp_path / "invalid.tar.gz")
    (source / "invalid.json").unlink()
    (source / "unrecognized.json").write_text(
        json.dumps({"schema_Name": "TaskProfileV1"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="missing string schema_name"):
        package_directory(source, tmp_path / "unrecognized.tar.gz")


def test_package_source_must_be_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be a directory"):
        package_directory(tmp_path / "missing", tmp_path / "out.tar.gz")
