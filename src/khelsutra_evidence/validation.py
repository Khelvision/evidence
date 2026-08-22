"""Structural, semantic, and public-safety validation."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .schemas import JsonObject, schemas_by_name, validator_for

_UNSAFE_KEYS = {
    "access_token",
    "api_key",
    "auth_token",
    "bucket_uri",
    "checkpoint_path",
    "client_secret",
    "credential",
    "credentials",
    "customer_email",
    "customer_id",
    "customer_name",
    "hidden_labels",
    "model_path",
    "object_uri",
    "participant_id",
    "password",
    "player_name",
    "private_endpoint",
    "private_key",
    "provider_endpoint",
    "provider_id",
    "raw_path",
    "secret",
    "secret_key",
    "storage_path",
    "storage_uri",
    "token",
}

_UNSAFE_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("common API token", re.compile(r"\b(?:ghp_|github_pat_|sk-[A-Za-z0-9_-]{12})[A-Za-z0-9_-]+")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "JSON Web Token",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ),
    (
        "signed URL credential",
        re.compile(
            r"[?&](?:token|sig|signature|x-amz-credential|x-amz-signature|"
            r"x-goog-signature)=[^&#\s]+",
            re.IGNORECASE,
        ),
    ),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "local Unix path",
        re.compile(r"(?:^|[\s(\[\"'=]|file://)/(?:home|Users|mnt|var/lib)/[^\s)\]}>\"']+"),
    ),
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

_COMMERCIALIZATION_CATEGORIES = {
    "application_code",
    "base_model",
    "checkpoint",
    "training_data",
    "evaluation_data",
    "media",
    "hosted_api",
    "codec",
    "output_redistribution",
}

_IGNORED_JSON_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}


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


def json_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return [
        path
        for path in sorted(root.rglob("*.json"))
        if not _is_ignored_json_path(path.relative_to(root))
    ]


def _is_ignored_json_path(relative: Path) -> bool:
    return any(
        part in _IGNORED_JSON_DIRECTORIES or part.startswith(".venv") or part.endswith(".egg-info")
        for part in relative.parts[:-1]
    )


def iter_json_documents(root: Path) -> Iterator[tuple[Path, JsonObject]]:
    for path in json_paths(root):
        yield path, load_json(path)


def validate_json_document(document: JsonObject) -> list[ValidationIssue]:
    if "$schema" not in document and "$id" not in document:
        return validate_document(document)

    issues: list[ValidationIssue] = []
    if document.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        issues.append(ValidationIssue("$schema", "must declare JSON Schema Draft 2020-12"))
    if not isinstance(document.get("$id"), str):
        issues.append(ValidationIssue("$id", "missing string JSON Schema identifier"))
    if issues:
        return issues
    try:
        Draft202012Validator.check_schema(document)
    except SchemaError as exc:
        return [ValidationIssue("$schema", f"invalid JSON Schema: {exc.message}")]
    return []


def validate_path(root: Path) -> dict[str, list[ValidationIssue]]:
    results: dict[str, list[ValidationIssue]] = {}
    for path, document in iter_json_documents(root):
        issues = validate_json_document(document)
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
            for label, pattern in _UNSAFE_PATTERNS:
                if pattern.search(key):
                    issues.append(ValidationIssue(child_path, f"field name contains {label}"))
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
    payload = {
        "plan_id": document["plan_id"],
        "items": document["items"],
        "rendition": document["rendition"],
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical_plan_digest(document: JsonObject) -> str:
    fields = (
        "plan_id",
        "actor_role",
        "workspace_id",
        "instruction",
        "scope",
        "filters",
        "transformations",
        "permission_checks",
        "output",
        "ambiguities",
        "execution_status",
        "human_decision_authority",
    )
    payload = {field: document[field] for field in fields}
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
        "CoachInstructionPlanV1": _plan_issues,
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
    issues: list[ValidationIssue] = []
    categories = [component["category"] for component in document["components"]]
    if len(categories) != len(set(categories)):
        issues.append(ValidationIssue("components", "commercialization categories must be unique"))
    missing = sorted(_COMMERCIALIZATION_CATEGORIES - set(categories))
    if missing:
        issues.append(
            ValidationIssue(
                "components", "missing commercialization categories: " + ", ".join(missing)
            )
        )
    declared = document["overall_status"]
    statuses = {component["status"] for component in document["components"]}
    expected = (
        "unknown"
        if "unknown" in statuses
        else "restricted"
        if "restricted" in statuses
        else "verified_clear"
    )
    if declared != expected:
        issues.append(
            ValidationIssue("overall_status", f"must be {expected!r} from component states")
        )
    return issues


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
        enumerate(document["rallies"]),
        key=lambda pair: (
            pair[1]["target_court_id"],
            pair[1]["start_frame"],
            pair[1]["end_frame"],
        ),
    )
    previous_end_by_court: dict[str, int] = {}
    for index, rally in ordered:
        if rally["rally_id"] in ids:
            issues.append(ValidationIssue(f"rallies.{index}.rally_id", "must be unique"))
        ids.add(rally["rally_id"])
        if rally["end_frame"] <= rally["start_frame"]:
            issues.append(
                ValidationIssue(f"rallies.{index}.end_frame", "must be after start_frame")
            )
        court = rally["target_court_id"]
        if rally["start_frame"] < previous_end_by_court.get(court, 0):
            issues.append(ValidationIssue(f"rallies.{index}", "rallies must not overlap"))
        previous_end_by_court[court] = max(
            int(rally["end_frame"]), previous_end_by_court.get(court, 0)
        )
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


def _plan_issues(document: JsonObject) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected = canonical_plan_digest(document)
    if document["plan_digest"]["value"] != expected:
        issues.append(
            ValidationIssue("plan_digest.value", f"must equal canonical plan digest {expected}")
        )
    has_ambiguity = bool(document["ambiguities"])
    status = document["execution_status"]
    if has_ambiguity and status != "requires_clarification":
        issues.append(
            ValidationIssue(
                "execution_status", "must require clarification while ambiguities remain"
            )
        )
    if not has_ambiguity and status == "requires_clarification":
        issues.append(
            ValidationIssue("execution_status", "cannot require clarification without ambiguities")
        )
    purposes = [check["purpose"] for check in document["permission_checks"]]
    if len(purposes) != len(set(purposes)):
        issues.append(ValidationIssue("permission_checks", "purposes must be unique"))
    for index, check in enumerate(document["permission_checks"]):
        if check["granted"] and "grant_ref" not in check:
            issues.append(
                ValidationIssue(
                    f"permission_checks.{index}.grant_ref",
                    "is required when a permission is granted",
                )
            )
    service_checks = [
        check for check in document["permission_checks"] if check["purpose"] == "service_operation"
    ]
    if status in {"ready", "partial_supported"} and not any(
        check["granted"] for check in service_checks
    ):
        issues.append(
            ValidationIssue(
                "permission_checks", "ready execution requires a granted service_operation"
            )
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
    issues: list[ValidationIssue] = []
    if document["available_match_count"] > document["requested_match_count"]:
        issues.append(
            ValidationIssue("available_match_count", "cannot exceed requested_match_count")
        )
    if (
        document["available_match_count"] < document["requested_match_count"]
        and not document["omissions"]
    ):
        issues.append(
            ValidationIssue("omissions", "must explain why fewer than the requested matches exist")
        )
    first_playable = document.get("first_playable_ref")
    if first_playable is not None and first_playable not in document["result_artifacts"]:
        issues.append(
            ValidationIssue("first_playable_ref", "must also be listed in result_artifacts")
        )
    return issues


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
