"""Project a private evidence superset into its deterministic public record."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .schemas import JsonObject
from .validation import safety_issues, validate_document

PRIVATE_RECORD_SCHEMA_NAME = "PrivateEvidenceRecordV1"

_MEDIA_TYPE_PREFIXES = ("audio/", "image/", "video/")

# Shorter private values collide with ordinary vocabulary often enough that an echo check on them
# would refuse honest records instead of leaking ones.
_ECHO_MIN_LENGTH = 12


@dataclass(frozen=True)
class ProjectionRefusal:
    """One machine-readable reason why a private record may not be published."""

    reason: str
    path: str
    message: str

    def render(self) -> str:
        location = f" at {self.path}" if self.path else ""
        return f"{self.reason}{location}: {self.message}"


def canonical_public_bytes(public: JsonObject) -> bytes:
    """Return the exact bytes a public record is published as."""
    return json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def public_record_digest(public: JsonObject) -> str:
    return hashlib.sha256(canonical_public_bytes(public)).hexdigest()


def projection_refusals(record: JsonObject) -> list[ProjectionRefusal]:
    """Return every reason the record may not be projected, or an empty list."""
    envelope = _envelope_refusals(record)
    if envelope:
        return envelope

    public: JsonObject = record["public"]
    refusals = _public_contract_refusals(public)
    refusals.extend(
        ProjectionRefusal("unsafe_public_value", issue.path, issue.message)
        for issue in safety_issues(public, "public")
    )
    refusals.extend(_media_refusals(record, public))
    refusals.extend(_echo_refusals(record, public))
    refusals.extend(_digest_refusals(record, public))
    return refusals


def project_record(record: JsonObject) -> bytes:
    """Return the publishable bytes, or raise if any refusal applies."""
    refusals = projection_refusals(record)
    if refusals:
        raise ValueError(
            "publication refused: " + "; ".join(refusal.render() for refusal in refusals)
        )
    return canonical_public_bytes(record["public"])


def _envelope_refusals(record: JsonObject) -> list[ProjectionRefusal]:
    if record.get("schema_name") != PRIVATE_RECORD_SCHEMA_NAME:
        return [
            ProjectionRefusal(
                "envelope_invalid",
                "schema_name",
                f"projection input must be a {PRIVATE_RECORD_SCHEMA_NAME} document",
            )
        ]
    return [
        ProjectionRefusal("envelope_invalid", issue.path, issue.message)
        for issue in validate_document(record)
    ]


def _public_contract_refusals(public: JsonObject) -> list[ProjectionRefusal]:
    if public.get("schema_name") == PRIVATE_RECORD_SCHEMA_NAME:
        return [
            ProjectionRefusal(
                "public_schema_drift",
                "public.schema_name",
                "a private record cannot be published as its own public projection",
            )
        ]
    return [
        ProjectionRefusal(
            "public_schema_drift",
            f"public.{issue.path}" if issue.path else "public",
            issue.message,
        )
        for issue in validate_document(public)
    ]


def _media_refusals(record: JsonObject, public: JsonObject) -> list[ProjectionRefusal]:
    authorizations = {str(entry["artifact_id"]): entry for entry in record["media_authorizations"]}
    referenced = _referenced_artifacts(public)
    refusals = [
        ProjectionRefusal(
            "dead_media_authorization",
            f"media_authorizations.{artifact_id}",
            "authorizes an artifact the projection never references",
        )
        for artifact_id in sorted(set(authorizations) - set(referenced))
    ]

    for artifact_id, paths in sorted(referenced.items()):
        if not paths:
            continue
        path = paths[0]
        entry = authorizations.get(artifact_id)
        if entry is None:
            refusals.append(
                ProjectionRefusal(
                    "unauthorized_media",
                    path,
                    f"media artifact {artifact_id!r} has no media authorization",
                )
            )
            continue
        grant = str(entry["publication_grant"])
        if grant != "verified_clear":
            refusals.append(
                ProjectionRefusal(
                    "unauthorized_media",
                    path,
                    f"publication grant for {artifact_id!r} is {grant!r}, not 'verified_clear'",
                )
            )
        if not any(
            purpose["purpose"] == "public_evidence" and purpose["granted"]
            for purpose in entry["purpose_grants"]
        ):
            refusals.append(
                ProjectionRefusal(
                    "unauthorized_media",
                    path,
                    f"media artifact {artifact_id!r} has no granted public_evidence purpose",
                )
            )
    return refusals


def _referenced_artifacts(public: JsonObject) -> dict[str, list[str]]:
    """Map every referenced artifact id to the projection paths that publish it as media."""
    referenced: dict[str, list[str]] = {}
    for path, value in _walk(public, "public"):
        if not isinstance(value, dict):
            continue
        artifact_id = value.get("artifact_id")
        if not isinstance(artifact_id, str) or "digest" not in value:
            continue
        media_paths = referenced.setdefault(artifact_id, [])
        media_type = value.get("media_type")
        if isinstance(media_type, str) and media_type.casefold().startswith(_MEDIA_TYPE_PREFIXES):
            media_paths.append(path)
    return referenced


def _echo_refusals(record: JsonObject, public: JsonObject) -> list[ProjectionRefusal]:
    private_values = {
        value
        for _, value in _walk(record["private_extensions"], "private_extensions")
        if isinstance(value, str) and len(value) >= _ECHO_MIN_LENGTH
    }
    if not private_values:
        return []
    refusals: list[ProjectionRefusal] = []
    for path, value in _walk(public, "public"):
        if not isinstance(value, str):
            continue
        for private_value in sorted(private_values):
            if private_value in value:
                refusals.append(
                    ProjectionRefusal(
                        "private_value_echo",
                        path,
                        "repeats a private_extensions value; a value that belongs in public "
                        "evidence is not a private extension",
                    )
                )
    return refusals


def _digest_refusals(record: JsonObject, public: JsonObject) -> list[ProjectionRefusal]:
    declared = str(record["projection"]["public_record_digest"]["value"])
    expected = public_record_digest(public)
    if declared == expected:
        return []
    return [
        ProjectionRefusal(
            "projection_digest_mismatch",
            "projection.public_record_digest.value",
            f"must equal the canonical public record digest {expected}",
        )
    ]


def _walk(value: Any, path: str) -> Iterator[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
