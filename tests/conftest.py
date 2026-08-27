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
def load_example(examples_root: Path):
    def load(relative: str) -> dict[str, Any]:
        return copy.deepcopy(json.loads((examples_root / relative).read_text(encoding="utf-8")))

    return load


@pytest.fixture
def load_fixture(fixtures_root: Path):
    def load(relative: str) -> dict[str, Any]:
        return copy.deepcopy(json.loads((fixtures_root / relative).read_text(encoding="utf-8")))

    return load
