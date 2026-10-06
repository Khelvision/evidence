"""Heuristic IP disclosure review; independent of credentials and media-rights validation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DisclosureControls:
    enabled: bool = True
    mode: str = "observe"
    recipes: bool = True
    private_references: bool = True
    model_assets: bool = True
    reviewed_sha256: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: dict[str, Any]) -> DisclosureControls:
        known = {
            "enabled",
            "mode",
            "recipes",
            "private_references",
            "model_assets",
            "reviewed_sha256",
        }
        if value.keys() - known:
            raise ValueError("unknown disclosure control")
        flags: dict[str, bool] = {}
        for name in ("enabled", "recipes", "private_references", "model_assets"):
            flag = value.get(name, True)
            if type(flag) is not bool:
                raise ValueError(f"{name} must be a JSON boolean")
            flags[name] = flag
        mode = value.get("mode", "observe")
        if mode not in ("off", "observe", "enforce"):
            raise ValueError("disclosure mode must be off, observe, or enforce")
        reviewed = value.get("reviewed_sha256", [])
        if not isinstance(reviewed, list) or len(reviewed) > 500:
            raise ValueError("reviewed_sha256 must be a bounded digest list")
        if any(not isinstance(d, str) or not re.fullmatch(r"[0-9a-f]{64}", d) for d in reviewed):
            raise ValueError("reviewed_sha256 requires exact lowercase SHA256 digests")
        return cls(
            enabled=flags["enabled"],
            mode=mode,
            recipes=flags["recipes"],
            private_references=flags["private_references"],
            model_assets=flags["model_assets"],
            reviewed_sha256=tuple(reviewed),
        )


_RECIPES = re.compile(
    r"\bQwen\d[\w.-]*-\d+B\b|\bR\d+\s+LoRA\b|"
    r"\bLoRA\b.{0,40}\brank\s*[=:]?\s*\d+|"
    r"\b[\d,]+\s+training windows\b|"
    r"\bmerge rule\b.{0,120}\b\d+(?:\.\d+)?\s+seconds\b|"
    r"\b\d+(?:\.\d+)?\s*(?:fps|frames per second)\b.{0,120}\bJPEG\b"
    r".{0,40}(?:quality\s*[=:]?\s*\d+|q\d+)",
    re.IGNORECASE | re.DOTALL,
)
_PRIVATE = re.compile(r"https?://[^\s)\"<>]*(?:\.ts\.net|\.tail[\w-]*\.ts\.net)[^\s)\"<>]*")
_TEXT = {".md", ".json", ".html", ".txt", ".yaml", ".yml"}
_MODEL = {".onnx", ".tflite", ".safetensors", ".pt", ".pth"}


def scan_disclosures(root: Path, controls: DisclosureControls) -> list[dict[str, Any]]:
    """Return locations/categories only; never echo the matched proprietary text."""
    if not controls.enabled or controls.mode == "off":
        return []
    if not root.exists():
        raise ValueError("disclosure scan root is missing")
    root = root.resolve()
    paths = sorted(root.rglob("*")) if root.is_dir() else [root]
    findings: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(root).as_posix() if root.is_dir() else path.name
        if any(
            part.startswith(".") or part in {"dist", "node_modules", "__pycache__"}
            for part in Path(relative).parts
        ):
            continue
        if path.suffix.lower() not in _TEXT | _MODEL:
            continue
        if path.is_symlink():
            findings.append({"path": relative, "line": 1, "reason": "symlink_not_reviewed"})
            continue
        if not path.is_file():
            continue
        if path.stat().st_size > 4 << 20:
            findings.append({"path": relative, "line": 1, "reason": "oversized_file_not_reviewed"})
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() in controls.reviewed_sha256:
            continue
        if path.suffix.lower() in _MODEL:
            if controls.model_assets:
                findings.append({"path": relative, "line": 1, "reason": "model_asset"})
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            findings.append({"path": relative, "line": 1, "reason": "non_utf8_not_reviewed"})
            continue
        for enabled, pattern, reason in (
            (controls.recipes, _RECIPES, "model_or_training_recipe"),
            (controls.private_references, _PRIVATE, "private_service_reference"),
        ):
            if enabled:
                findings.extend(
                    {"path": relative, "line": text.count("\n", 0, m.start()) + 1, "reason": reason}
                    for m in pattern.finditer(text)
                )
    return findings
