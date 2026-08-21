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
def load_example(examples_root: Path):
    def load(relative: str) -> dict[str, Any]:
        return copy.deepcopy(json.loads((examples_root / relative).read_text(encoding="utf-8")))

    return load
