"""Decide whether a proposed release's media may be published at all.

A release names sample IDs. Each is footage of real people in a real venue, and the right to publish
it exists only as a set of documents somebody obtained. This module compares the two and
reports what is missing, so "get the media grants" becomes a checklist rather than a judgement made
at publication time.

It answers one question — *is every sample in this release covered by grants that permit public
evidence* — and it fails closed. It cannot read a consent document or tell you whether it says what
its holder claims.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .schemas import JsonObject
from .validation import validate_document

MEDIA_GRANT_SCHEMA_NAME = "MediaGrantV1"
RELEASE_SCHEMA_NAME = "EvidenceReleaseV1"
DISTRIBUTION_SCHEMA_NAME = "ReleaseDistributionV1"

# A release that hands over no footage does not exercise the right to publish that footage. Every
# other requirement still applies: the people in it are still being measured in public.
_RELAXED_BY_EVIDENCE_ONLY = ("publication_not_verified_clear",)

_RESOLVED_VENUE_STATES = {"verified_clear", "not_applicable"}


@dataclass(frozen=True)
class MediaGap:
    """One reason a sample is not cleared for publication."""

    sample_id: str
    requirement: str
    detail: str

    def render(self) -> str:
        return f"{self.sample_id}: {self.requirement}: {self.detail}"


def grant_gaps(grant: JsonObject, *, evidence_only: bool = False) -> list[MediaGap]:
    """Return every reason this grant does not clear its sample for public evidence.

    Under `evidence_only` the source media is not handed over, so the grant to publish that media is
    not exercised and is not required. Consent to be measured in public still is.
    """
    sample_id = str(grant["sample_id"])
    gaps: list[MediaGap] = []

    publication = str(grant["publication_grant"])
    if publication != "verified_clear" and not evidence_only:
        gaps.append(
            MediaGap(
                sample_id,
                "publication_not_verified_clear",
                f"publication grant is {publication!r}; unknown never renders as clear",
            )
        )

    venue = grant["venue_permission"]
    venue_state = str(venue["state"])
    if venue_state not in _RESOLVED_VENUE_STATES:
        gaps.append(
            MediaGap(
                sample_id,
                "venue_permission_unresolved",
                f"venue permission is {venue_state!r}",
            )
        )

    participants = grant["participants"]
    if not participants:
        gaps.append(
            MediaGap(
                sample_id,
                "no_participants_recorded",
                "the grant records no participant; footage with nobody in it and footage nobody "
                "reviewed look identical here, so a human must say which this is",
            )
        )

    for participant in participants:
        handle = str(participant["participant_handle"])
        if participant.get("withdrawn"):
            gaps.append(MediaGap(sample_id, "participant_withdrawn", f"{handle} withdrew consent"))
            continue
        if not _grants_public_evidence(participant):
            gaps.append(
                MediaGap(
                    sample_id,
                    "participant_consent_missing_public_evidence",
                    f"{handle} has no granted public_evidence purpose",
                )
            )
        if participant.get("guardian_authorization_required") and (
            "guardian_authorization_ref" not in participant
        ):
            gaps.append(
                MediaGap(
                    sample_id,
                    "guardian_authorization_missing",
                    f"{handle} requires guardian or legal authorization and none is bound",
                )
            )
    return gaps


def _grants_public_evidence(participant: JsonObject) -> bool:
    return any(
        purpose["purpose"] == "public_evidence" and purpose["granted"]
        for purpose in participant["purpose_grants"]
    )


def preflight(
    release: JsonObject, grants: list[JsonObject], distribution: JsonObject | None = None
) -> JsonObject:
    """Report, per sample in the release, whether its media may be published.

    Without a distribution declaration the strictest reading applies: assume the release hands over
    the footage. Publishing less than that is a claim somebody has to make on the record.
    """
    _require(release, RELEASE_SCHEMA_NAME, "release")
    for grant in grants:
        _require(grant, MEDIA_GRANT_SCHEMA_NAME, "media grant")
    if distribution is not None:
        _require(distribution, DISTRIBUTION_SCHEMA_NAME, "release distribution")
        if str(distribution["release_id"]) != str(release["release_id"]):
            raise ValueError("release distribution names a different release")
    mode = str(distribution["distribution"]) if distribution else "media_included"
    evidence_only = mode == "evidence_only"

    by_sample: dict[str, JsonObject] = {}
    duplicates: list[str] = []
    for grant in grants:
        sample_id = str(grant["sample_id"])
        if sample_id in by_sample:
            duplicates.append(sample_id)
        by_sample[sample_id] = grant

    samples: list[JsonObject] = []
    for sample_id in release["sample_ids"]:
        covering = by_sample.get(str(sample_id))
        if covering is None:
            gaps = [MediaGap(str(sample_id), "no_grant", "no MediaGrantV1 covers this sample")]
            permits: JsonObject = {}
        else:
            gaps = grant_gaps(covering, evidence_only=evidence_only)
            permits = {
                "training": bool(covering["training_permitted"]),
                "rehosting": bool(covering["rehosting_permitted"]),
                "custody": str(covering["custody"]),
            }
        samples.append(
            {
                "sample_id": str(sample_id),
                "cleared": not gaps,
                "gaps": [{"requirement": gap.requirement, "detail": gap.detail} for gap in gaps],
                "permits": permits,
            }
        )

    unused = sorted(set(by_sample) - {str(s) for s in release["sample_ids"]})
    cleared = [entry for entry in samples if entry["cleared"]]
    return {
        "release_id": str(release["release_id"]),
        "registry": str(release["registry"]),
        "distribution": mode,
        "distribution_declared": distribution is not None,
        "relaxed_requirements": list(_RELAXED_BY_EVIDENCE_ONLY) if evidence_only else [],
        "samples": samples,
        "unused_grants": unused,
        "duplicate_grants": sorted(set(duplicates)),
        "summary": {
            "requested": len(samples),
            "cleared": len(cleared),
            "blocked": len(samples) - len(cleared),
        },
    }


def _require(document: JsonObject, schema_name: str, label: str) -> None:
    issues = validate_document(document)
    if issues:
        raise ValueError(f"invalid {label}: " + "; ".join(issue.render() for issue in issues))
    if document["schema_name"] != schema_name:
        raise ValueError(f"{label} input must use {schema_name}")


def collect_grants(documents: Iterable[tuple[Any, JsonObject]]) -> list[JsonObject]:
    """Keep the MediaGrantV1 documents from a directory scan, in path order.

    A grants directory is a working folder, not a curated one. Anything that is not a media grant is
    ignored here rather than refused, because the release is what decides which samples matter.
    """
    return [
        document
        for _, document in documents
        if isinstance(document, dict) and document.get("schema_name") == MEDIA_GRANT_SCHEMA_NAME
    ]
