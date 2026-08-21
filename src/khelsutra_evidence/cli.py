"""Command-line interface for the public evidence framework."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from .comparison import compare_runs
from .packaging import package_directory
from .scoring import score_rallies
from .templates import initialize_workspace
from .validation import load_json, validate_document, validate_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evidence", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a synthetic starter workspace")
    init.add_argument("destination", type=Path)

    verify = subparsers.add_parser("verify", help="validate evidence documents")
    verify.add_argument("path", type=Path)

    score = subparsers.add_parser("score", help="score rally-boundary predictions")
    score.add_argument("truth", type=Path)
    score.add_argument("prediction", type=Path)
    score.add_argument("--tolerance-frames", type=int, default=15)
    score.add_argument("--output", type=Path)

    compare = subparsers.add_parser("compare", help="compare two SystemRunV1 documents")
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)
    compare.add_argument("--output", type=Path)

    package = subparsers.add_parser("package", help="validate and create a deterministic archive")
    package.add_argument("source", type=Path)
    package.add_argument("destination", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            files = initialize_workspace(args.destination)
            _emit({"status": "created", "files": [str(path) for path in files]})
        elif args.command == "verify":
            failures = validate_path(args.path)
            if failures:
                _emit(
                    {
                        "status": "invalid",
                        "files": {
                            path: [issue.render() for issue in issues]
                            for path, issues in failures.items()
                        },
                    }
                )
                return 1
            count = sum(1 for _ in _documents(args.path))
            if count == 0:
                raise ValueError("no schema documents found")
            _emit({"status": "valid", "documents": count})
        elif args.command == "score":
            result = score_rallies(
                load_json(args.truth), load_json(args.prediction), args.tolerance_frames
            )
            _require_result_valid(result)
            _write_or_emit(result, args.output)
        elif args.command == "compare":
            result = compare_runs(load_json(args.left), load_json(args.right))
            _require_result_valid(result)
            _write_or_emit(result, args.output)
        elif args.command == "package":
            digest = package_directory(args.source, args.destination)
            _emit({"status": "packaged", "path": str(args.destination), "sha256": digest})
        else:
            raise AssertionError(f"unhandled command {args.command}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _emit({"status": "error", "message": str(exc)}, stream=sys.stderr)
        return 2
    return 0


def _documents(path: Path) -> list[Path]:
    paths = [path] if path.is_file() else sorted(path.rglob("*.json"))
    result = []
    for candidate in paths:
        try:
            if "schema_name" in load_json(candidate):
                result.append(candidate)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return result


def _require_result_valid(document: dict[str, object]) -> None:
    issues = validate_document(document)
    if issues:
        raise ValueError(
            "generated invalid result: " + "; ".join(issue.render() for issue in issues)
        )


def _write_or_emit(document: dict[str, object], output: Path | None) -> None:
    if output is None:
        _emit(document)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _emit(document: object, stream: TextIO | None = None) -> None:
    destination = sys.stdout if stream is None else stream
    print(json.dumps(document, indent=2, sort_keys=True), file=destination)
