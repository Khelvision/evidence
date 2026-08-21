"""Structural, semantic, and public-safety validation."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import JsonObject, schemas_by_name, validator_for

_UNSAFE_KEYS = {
    "api_key",
    "credential",
    "credentials",
    "customer_email",
    "customer_name",
    "hidden_labels",
    "private_endpoint",
    "provider_endpoint",
    "provider_id",
    "raw_path",
    "secret",
    "token",
}

_UNSAFE_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("common API token", re.compile(r"\b(?:ghp_|github_pat_|sk-[A-Za-z0-9_-]{12})[A-Za-z0-9_-]+")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("local Unix path", re.compile(r"(?:^|\s)/(?:home|Users|mnt|var/lib)/[^\s]+")),
    ("local Windows path", re.compile(r"\b[A-Za-z]:\\(?:Users|Documents|AppData)\\")),
    ("tailnet endpoint", re.compile(r"\b[A-Za-z0-9.-]+\.ts\.net\b")),
    ("loopback endpoint", re.compile(r"\b(?:localhost|127\.0\.0\.1)(?::\d+)?\b")),
    (
        "private IPv4 endpoint",
        re.compile(
            r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
            r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
        ),
    ),
)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def render(self) -> str:
        return f"{self.path}: {self.message}" if self.path else self.message


def load_json(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def validate_document(document: JsonObject) -> list[ValidationIssue]:
    name = document.get("schema_name")
    if not isinstance(name, str):
        return [ValidationIssue("schema_name", "missing string schema_name")]
    if name not in schemas_by_name():
        return [ValidationIssue("schema_name", f"unknown schema {name!r}")]

    issues: list[ValidationIssue] = []
    validator = validator_for(name)
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path)):
        path = ".".join(str(part) for part in error.absolute_path)
        issues.append(ValidationIssue(path, error.message))
    if not issues:
        issues.extend(_semantic_issues(document))
    return issues


def iter_schema_documents(root: Path) -> Iterator[tuple[Path, JsonObject]]:
    paths = [root] if root.is_file() else sorted(root.rglob("*.json"))
    for path in paths:
        document = load_json(path)
        if "schema_name" in document:
            yield path, document


def validate_path(root: Path) -> dict[str, list[ValidationIssue]]:
    results: dict[str, list[ValidationIssue]] = {}
    for path, document in iter_schema_documents(root):
        issues = validate_document(document)
        if issues:
            results[str(path)] = issues
    return results


def safety_issues(value: Any, path: str = "$") -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.casefold() in _UNSAFE_KEYS:
                issues.append(
                    ValidationIssue(child_path, "private-only field name is not publishable")
                )
            issues.extend(safety_issues(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(safety_issues(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for label, pattern in _UNSAFE_PATTERNS:
            if pattern.search(value):
                issues.append(ValidationIssue(path, f"contains {label}"))
    return issues


def canonical_recipe_digest(document: JsonObject) -> str:
    import hashlib

    payload = {
        "plan_id": document["plan_id"],
        "items": document["items"],
        "rendition": document["rendition"],
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _semantic_issues(document: JsonObject) -> list[ValidationIssue]:
    name = document["schema_name"]
    checks = {
        "ScenarioProfileV1": _scenario_issues,
        "CommercializationReadinessV1": _commercialization_issues,
        "CostReceiptV1": _cost_issues,
        "RallyBoundarySetV1": _rally_set_issues,
        "SystemRunV1": _system_run_issues,
        "EvidenceReleaseV1": _release_issues,
        "OwnerAdaptationRunV1": _adaptation_issues,
        "EvidenceRecipeV1": _recipe_issues,
        "CoachAgentRunReceiptV1": _agent_receipt_issues,
    }
    issues = checks.get(name, lambda _: [])(document)
    issues.extend(_authority_issues(document))
    return issues


def _scenario_issues(document: JsonObject) -> list[ValidationIssue]:
    if document["simultaneously_active_games"] > document["visible_courts"]:
        return [
            ValidationIssue(
                "simultaneously_active_games", "cannot exceed the number of visible courts"
            )
        ]
    return []


def _commercialization_issues(document: JsonObject) -> list[ValidationIssue]:
    declared = document.get("overall_status")
    if declared is None:
        return []
    statuses = {component["status"] for component in document["components"]}
    expected = (
        "unknown"
        if "unknown" in statuses
        else "restricted"
        if "restricted" in statuses
        else "verified_clear"
    )
    if declared != expected:
        return [ValidationIssue("overall_status", f"must be {expected!r} from component states")]
    return []


def _rate_issue(
    document: JsonObject, field: str, numerator: float, denominator: float
) -> list[ValidationIssue]:
    expected = numerator * 3600.0 / denominator
    if not math.isclose(float(document[field]), expected, rel_tol=1e-9, abs_tol=1e-9):
        return [ValidationIssue(field, f"must equal raw numerator/denominator ({expected:.12g})")]
    return []


def _cost_issues(document: JsonObject) -> list[ValidationIssue]:
    source = float(document["source_seconds"])
    accepted = float(document["accepted_source_seconds"])
    issues: list[ValidationIssue] = []
    if accepted > source:
        issues.append(ValidationIssue("accepted_source_seconds", "cannot exceed source_seconds"))
    issues.extend(
        _rate_issue(
            document, "inference_usd_per_source_hour", float(document["inference_usd"]), source
        )
    )
    issues.extend(
        _rate_issue(
            document,
            "accelerator_seconds_per_source_hour",
            float(document["accelerator_seconds"]),
            source,
        )
    )
    issues.extend(
        _rate_issue(
            document, "wall_seconds_per_source_hour", float(document["wall_seconds"]), source
        )
    )
    issues.extend(
        _rate_issue(
            document,
            "total_cost_usd_per_accepted_source_hour",
            float(document["total_cost_usd"]),
            accepted,
        )
    )
    if "manual_minutes_per_source_hour" in document:
        issues.extend(
            _rate_issue(
                document,
                "manual_minutes_per_source_hour",
                float(document["manual_review_minutes"]),
                source,
            )
        )
    return issues


def _rally_set_issues(document: JsonObject) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    ids: set[str] = set()
    ordered = sorted(
        document["rallies"], key=lambda rally: (rally["start_frame"], rally["end_frame"])
    )
    for index, rally in enumerate(ordered):
        if rally["rally_id"] in ids:
            issues.append(ValidationIssue(f"rallies.{index}.rally_id", "must be unique"))
        ids.add(rally["rally_id"])
        if rally["end_frame"] <= rally["start_frame"]:
            issues.append(
                ValidationIssue(f"rallies.{index}.end_frame", "must be after start_frame")
            )
        if index and rally["start_frame"] < ordered[index - 1]["end_frame"]:
            issues.append(ValidationIssue(f"rallies.{index}", "rallies must not overlap"))
    return issues


def _system_run_issues(document: JsonObject) -> list[ValidationIssue]:
    ids = [sample["sample_id"] for sample in document["samples"]]
    issues = []
    if len(ids) != len(set(ids)):
        issues.append(ValidationIssue("samples", "sample_id values must be unique"))
    has_nonaccepted = any(sample["status"] != "accepted" for sample in document["samples"])
    if has_nonaccepted and not document["failures_included"]:
        issues.append(
            ValidationIssue(
                "failures_included", "must be true when non-accepted samples are present"
            )
        )
    return issues


def _release_issues(document: JsonObject) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if document["release_class"] == "demonstration" and not document["exposed_before_freeze"]:
        issues.append(
            ValidationIssue("exposed_before_freeze", "demonstrations must be marked exposed")
        )
    if document["release_class"] == "blind" and document["exposed_before_freeze"]:
        issues.append(
            ValidationIssue(
                "exposed_before_freeze", "blind releases cannot be exposed before freeze"
            )
        )
    if document["registry"] == "official" and not document["failures_included"]:
        issues.append(
            ValidationIssue("failures_included", "official releases must include failures")
        )
    if document["registry"] == "official" and document["media_license_status"] == "unknown":
        issues.append(
            ValidationIssue(
                "media_license_status", "official publication cannot use unknown media rights"
            )
        )
    return issues


def _adaptation_issues(document: JsonObject) -> list[ValidationIssue]:
    training = set(document["training_sample_ids"])
    heldout = set(document["heldout_sample_ids"])
    issues: list[ValidationIssue] = []
    if training & heldout:
        issues.append(
            ValidationIssue("heldout_sample_ids", "must be disjoint from training_sample_ids")
        )
    if document["owner_metric_before"]["name"] != document["owner_metric_after"]["name"]:
        issues.append(
            ValidationIssue("owner_metric_after.name", "must match owner_metric_before.name")
        )
    if document["decision"] != "pending" and "decision_authority" not in document:
        issues.append(
            ValidationIssue("decision_authority", "is required for promoted or rejected candidates")
        )
    return issues


def _recipe_issues(document: JsonObject) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    orders = [item["order"] for item in document["items"]]
    if orders != list(range(len(orders))):
        issues.append(ValidationIssue("items", "order values must be contiguous and start at zero"))
    expected = canonical_recipe_digest(document)
    if document["recipe_digest"]["value"] != expected:
        issues.append(
            ValidationIssue("recipe_digest.value", f"must equal canonical recipe digest {expected}")
        )
    return issues


def _agent_receipt_issues(document: JsonObject) -> list[ValidationIssue]:
    if document["available_match_count"] > document["requested_match_count"]:
        return [ValidationIssue("available_match_count", "cannot exceed requested_match_count")]
    return []


def _authority_issues(value: Any, path: str = "$") -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(value, dict):
        authority = value.get("authority")
        if authority == "model_observation":
            if "model_id" not in value:
                issues.append(ValidationIssue(path, "model_observation requires model_id"))
            if "confidence" not in value:
                issues.append(ValidationIssue(path, "model_observation requires confidence"))
        for key, child in value.items():
            issues.extend(_authority_issues(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_authority_issues(child, f"{path}[{index}]"))
    return issues
