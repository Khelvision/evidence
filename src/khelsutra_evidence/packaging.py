"""Create deterministic, locally verifiable public evidence archives."""

from __future__ import annotations

import gzip
import hashlib
import io
import tarfile
from pathlib import Path

from .validation import load_json, safety_issues, validate_json_document

_ALLOWED_SUFFIXES = {".json", ".md", ".txt"}
_MAX_FILE_BYTES = 5 * 1024 * 1024
_PRIVATE_PACKAGE_SCHEMAS = frozenset({"MediaGrantV1", "PrivateEvidenceRecordV1"})


def package_directory(source: Path, destination: Path) -> str:
    if not source.is_dir():
        raise ValueError("package source must be a directory")
    files = _safe_files(source)
    if not files:
        raise ValueError("package source contains no supported files")
    _validate_files(files)

    destination.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with (
        gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0, filename="") as gzip_file,
        tarfile.open(fileobj=gzip_file, mode="w") as archive,
    ):
        for path in files:
            relative = path.relative_to(source).as_posix()
            data = path.read_bytes()
            info = tarfile.TarInfo(relative)
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    payload = buffer.getvalue()
    destination.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _safe_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symbolic links are not publishable: {path}")
        if path.is_dir():
            continue
        if path.suffix.casefold() not in _ALLOWED_SUFFIXES:
            raise ValueError(f"unsupported package file type: {path}")
        if path.stat().st_size > _MAX_FILE_BYTES:
            raise ValueError(f"package file exceeds {_MAX_FILE_BYTES} bytes: {path}")
        files.append(path)
    return files


def _validate_files(files: list[Path]) -> None:
    for path in files:
        if path.suffix.casefold() != ".json":
            text = path.read_text(encoding="utf-8")
            issues = safety_issues(text)
        else:
            document = load_json(path)
            issues = safety_issues(document)
            issues.extend(validate_json_document(document))
            schema_name = document.get("schema_name")
            if schema_name in _PRIVATE_PACKAGE_SCHEMAS:
                raise ValueError(
                    f"{path}: publication refused: {schema_name} is a private contract and "
                    "cannot enter a public package"
                )
            if schema_name == "SystemProvenanceV1":
                basis = document.get("disclosure_basis")
                if basis != "vendor_stated":
                    raise ValueError(
                        f"{path}: publication refused: a {basis!r} disclosure is this producer's "
                        "conclusion about a system rather than what its vendor stated, which is a "
                        "competitive claim and does not belong in a public evidence package"
                    )
        if issues:
            rendered = "; ".join(issue.render() for issue in issues)
            raise ValueError(f"{path}: publication refused: {rendered}")


def archive_members(path: Path) -> list[str]:
    with tarfile.open(path, mode="r:gz") as archive:
        return archive.getnames()
