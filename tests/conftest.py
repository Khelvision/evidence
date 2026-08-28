from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def examples_root() -> Path:
    return Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def fixtures_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def private_examples_root() -> Path:
    return Path(__file__).resolve().parents[1] / "private-examples"


@pytest.fixture
def load_example(examples_root: Path, private_examples_root: Path):
    """Load a shipped example from either root.

    The two roots differ in what may be published, not in what must be valid: `examples/` is the
    publishable set and `private-examples/` holds the contracts a producer keeps. `evidence package`
    is what enforces that boundary; this fixture only has to find the file.
    """

    def load(relative: str) -> dict[str, Any]:
        path = examples_root / relative
        if not path.exists():
            path = private_examples_root / relative
        return copy.deepcopy(json.loads(path.read_text(encoding="utf-8")))

    return load


@pytest.fixture
def load_fixture(fixtures_root: Path):
    def load(relative: str) -> dict[str, Any]:
        return copy.deepcopy(json.loads((fixtures_root / relative).read_text(encoding="utf-8")))

    return load
