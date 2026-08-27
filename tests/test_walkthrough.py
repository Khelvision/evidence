"""Execute the walkthrough so the documentation cannot drift from the tool.

Every ```bash block in `docs/WALKTHROUGH.md` runs in order in a scratch directory, and the block
that follows it is checked against what the command really printed. A block may declare the exit
status it expects with an info string such as ```bash exit=1, which is how the walkthrough shows a
refusal without pretending the command succeeded.

The walkthrough may abridge an output: a documented JSON object must be a *subset* of the real one.
It may not invent one.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
WALKTHROUGH = ROOT / "docs" / "WALKTHROUGH.md"
FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class Step:
    script: str
    expected_status: int
    documented_output: str | None


def _steps() -> list[Step]:
    fences = FENCE.findall(WALKTHROUGH.read_text(encoding="utf-8"))
    steps: list[Step] = []
    for index, (info, body) in enumerate(fences):
        if not info.startswith("bash"):
            continue
        status = re.search(r"exit=(\d+)", info)
        following = fences[index + 1] if index + 1 < len(fences) else None
        output = None
        if following is not None and not following[0].startswith("bash"):
            output = following[1]
        steps.append(Step(body, int(status.group(1)) if status else 0, output))
    return steps


def _subset(expected: Any, actual: Any, path: str = "$") -> list[str]:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: documented an object, command printed {type(actual).__name__}"]
        problems: list[str] = []
        for key, value in expected.items():
            if key not in actual:
                problems.append(f"{path}.{key}: documented but not printed")
            else:
                problems.extend(_subset(value, actual[key], f"{path}.{key}"))
        return problems
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return [f"{path}: documented {expected!r}, command printed {actual!r}"]
        problems = []
        for index, value in enumerate(expected):
            problems.extend(_subset(value, actual[index], f"{path}[{index}]"))
        return problems
    if expected != actual:
        return [f"{path}: documented {expected!r}, command printed {actual!r}"]
    return []


@pytest.fixture(scope="module")
def executed(tmp_path_factory: pytest.TempPathFactory) -> list[tuple[Step, str]]:
    workspace = tmp_path_factory.mktemp("walkthrough")
    shim = workspace / "bin"
    shim.mkdir()
    (shim / "evidence").write_text(
        f'#!/bin/sh\nexec "{sys.executable}" -m khelsutra_evidence "$@"\n', encoding="utf-8"
    )
    (shim / "evidence").chmod(0o755)
    # Coverage tracks this process, not the walkthrough's; leaving its hooks in the child makes it
    # write measurement files that cannot be combined with ours.
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE", "COVERAGE"))
    }
    environment["PATH"] = f"{shim}{os.pathsep}{environment.get('PATH', '')}"
    environment["LC_ALL"] = "C"

    results: list[tuple[Step, str]] = []
    for index, step in enumerate(_steps()):
        if step.script.strip().startswith("pip install"):
            # The reader installs the published package; the test exercises the tree it is reading.
            continue
        completed = subprocess.run(
            ["bash", "-uo", "pipefail", "-c", step.script],
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == step.expected_status, (
            f"step {index} expected exit {step.expected_status}, got {completed.returncode}\n"
            f"{step.script}\n{completed.stdout}\n{completed.stderr}"
        )
        results.append((step, completed.stdout + completed.stderr))
    return results


def test_walkthrough_runs_and_shows_a_real_refusal(executed: list[tuple[Step, str]]) -> None:
    assert len(executed) >= 10
    assert any(step.expected_status == 1 for step, _ in executed)


def test_documented_output_is_a_subset_of_real_output(executed: list[tuple[Step, str]]) -> None:
    checked = 0
    problems: list[str] = []
    for step, transcript in executed:
        if step.documented_output is None:
            continue
        documented = step.documented_output.strip()
        if not documented.startswith("{"):
            if documented.split()[0] not in transcript:
                problems.append(f"{step.script.strip()}: {documented!r} not in output")
            checked += 1
            continue
        printed = transcript[transcript.index("{") :] if "{" in transcript else "{}"
        found = _subset(json.loads(documented), json.loads(printed))
        problems.extend(f"{step.script.strip().splitlines()[-1]}: {problem}" for problem in found)
        checked += 1
    assert not problems, "\n".join(problems)
    assert checked >= 6, f"only {checked} documented outputs were checked"
