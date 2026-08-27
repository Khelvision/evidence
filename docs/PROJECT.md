# KhelSutra evidence delivery program

> **Status:** `IN PROGRESS` · **Owner:** Avi Dullu · **Created:** 2026-08-22 ·
> **Last updated:** 2026-08-27
>
> **Lifecycle:** `DRAFT -> IN PROGRESS -> DONE -> ARCHIVED`
>
> **Tracking anchor:** the progress table in section 5 is the source of truth for this repository.
> Each row is independently shippable and each implementation PR updates its own row and changelog.
>
> **Honesty note:** tracker rows project the state after their linked PR lands. Nothing in this file
> claims a public model result, media grant, paid run, deployment, or completed backup propagation.

## 1. Objective

Publish a local-first, independently usable evidence framework for sports-video systems without turning
a model score into a coaching claim. The framework makes task semantics, real capture conditions,
quality, cost, rights, failure modes, owner-model portability, and human authority machine-readable.

KhelSutra remains an AI agent for the coach, including a person coaching themselves. It is never the
coaching authority. The human chooses the objective, interprets the evidence, and decides what happens
next.

## 2. Repository boundary

This repository owns:

- public JSON Schemas and semantic validators;
- reference scoring, comparability, packaging, and deterministic safety checks;
- synthetic examples and separate official/community registries;
- public release manifests and the static evidence-site source; and
- this program tracker and release history.

Producer repositories own their own private receipts, model/runtime changes, corpus and media custody,
and CI integration. A producer obligation is linked here as an external dependency; this tracker does
not mark work complete on behalf of BHI, code-doot, the vault, an app, or another repository.

The BHI doctrine PR
[#1063](https://avis-pbook.tail651ec3.ts.net/Khelsutra/badminton-highlight-indexer/pulls/1063)
owns the engine/product wording and the coach-agent authority ratification. It does not own this
repository's KE-1 through KE-7 delivery state.

## 3. Locked evidence contracts

- Official and community evidence remain visibly separate.
- A comparability verdict explains whether artifacts are paired, quality-only paired, partially
  comparable, descriptive only, or incompatible; it does not certify a vendor or model.
- Derived metrics retain their raw numerators and denominators.
- Capture conditions include visible and active games/courts, target court, occlusion, lighting,
  camera motion, cuts, resolution, frame rate, audio availability, and duration where applicable.
- Licensing states are `verified_clear`, `restricted`, `unknown`, or `not_applicable`; unknown never
  renders green.
- Public records are allowlisted projections. Unknown private fields, secrets, private endpoints,
  customer identifiers, absolute paths, hidden labels, and unauthorized media fail publication.
- Demonstrations are permanently exposed and never become blind or sealed-primary evidence.
- Consent and participant age are separate. Every media use binds the exact consent, any required
  guardian or legal authorization, purpose, custody, and publication grants; age alone neither grants
  nor denies a use.
- A candidate model never promotes itself. Owner adaptation evidence requires disjoint held-out data,
  common-ruler non-regression, export, clean restore, replay, promotion, rollback, time, and cost.
- No service-level target is claimed before a frozen workload publishes measured distributions.

## 4. Release ladder

- **v0.1 demonstrations:** rights-cleared samples covering clean single court, imperfect fixed capture,
  and multiple active games. They are exposed examples, never blind evidence.
- **v0.2 blind challenge:** a frozen, rights-cleared multi-stratum inventory, two annotators, frozen
  scorer and engine, no train/select overlap, and every failure retained.
- **v0.3 ownership proof:** base-versus-owner-adapted evidence on disjoint held-out data plus portable
  export, restore, replay, promotion, and rollback.
- **v0.4 coach-agent proof:** the canonical coach-directed query produces an inspectable plan,
  content-addressed recipe, playable result, omissions, provenance, cost, and latency without issuing a
  coaching prescription.

No version number is a quality claim until its row closes with the required artifacts on the default
branch.

## 5. Deliverables and progress

Legend: `Pending`, `In progress`, `Complete`, `Blocked`. One independently shippable PR per row; do not
stack rows.

| ID | Deliverable | Depends on | Gate | Status | PR |
|---|---|---|---|---|---|
| KE-1 | Publish the initial schemas, CLI, scorer, comparability rationale, examples, community rules, static site source, Forgejo CI, ownership routing, and this tracker | BHI #1063 doctrine | BHI #1063 must land before this PR; exact-head verification is recorded on the PR | Complete | [#1](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/pulls/1) |
| KE-2a | Publish the private-superset/public-projection contract, the projector, and negative fixtures; producer integrations remain in their own repositories | KE-1 | Security review of the envelope classification, refusal reasons, and negative fixtures | Complete | — |
| KE-2b | Publish the language-neutral contract statement and portable conformance suite so Python is a supported verification route rather than a prerequisite | KE-2a | Architecture decision accepted by Avi; conformance corpus consumed by the Python tests | Pending | [issue #2](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/issues/2) |
| KE-3 | Publish the v0.1 demonstration release | KE-1, KE-2a | Exact media inventory, consent, purpose/publication grant, custody, redaction, and claims review | Blocked | — |
| KE-4 | Publish the frozen v0.2 blind challenge | KE-3 | Rights-cleared frozen inventory, two annotators, frozen scorer/engine, no train/select overlap | Pending | — |
| KE-5 | Publish the v0.3 owner-adaptation and portability proof | KE-2a | Authorized owner corpus, disjoint held-out ruler, and second clean environment | Pending | — |
| KE-6 | Publish the v0.4 coach-agent query proof | KE-2a | Governed player/match/outcome/shot metadata and deterministic recipe renderer | Pending | — |
| KE-7 | Publish the durable evidence site and release index | KE-1 | Explicit infrastructure/domain approval and source-driven deployment | Pending | — |

## 6. External gates

1. Repository initialization is complete: Avi created empty `main` commit
   `dd6b437959fa250ccba5afa13c3089430f5530da`, and KE-1 was rebased onto that exact head. Agents do
   not push directly to the default branch.
2. BHI #1063 must retain only BHI-owned doctrine and integration responsibilities and must not remain the
   canonical tracker for this repository.
3. Producer integrations update their producer-owned tracker or issue and link the exact merged revision
   here; a prose claim in this repository is not proof that private CI or receipts exist.
4. Exact media consent, purpose, custody, publication, and redaction authority is required before any
   real-media release. This program grants no Tier G access.
5. Paid inference or training requires a separate exact run plan, budget, durable observer/evidence, and
   verified provider zero state.
6. Site publication requires explicit infrastructure authority and a source-driven deployment path.
7. The Forgejo-to-GitHub backup mirror is failing and needs an owner decision on GitHub. Every scheduled
   push since KE-1 has been rejected: `PushRejected ... GH013: Repository rule violations found for
   refs/heads/codex/initial-evidence-framework ... GITHUB PUSH PROTECTION ... Push cannot contain
   secrets`, last attempted 2026-08-27T04:39:32+05:30. The flagged strings are the synthetic
   secret-shaped values in `tests/test_validation.py`, which exist so the public-safety scanner can be
   tested against them. They are reachable from merged history, so changing the current tip cannot clear
   them; only an owner action on the GitHub backup can. Agents do not push to GitHub.

## 7. Definition of Done

- [x] KE-1 contains the initial contracts, tooling, synthetic examples, registries, site source, and
  tracker, and the package installs and runs from a clean environment. This proposed diff projects the
  state after PR #1 lands.
- [x] GitHub Actions is disabled on the GitHub backup: `repos/Khelsutra/evidence/actions/permissions`
  returned `{"enabled": false}` and the repository reports no workflows, verified 2026-08-27.
- [ ] The exact Forgejo `main` head has **not** propagated to the GitHub backup. `Khelsutra/evidence` on
  GitHub still has zero branches; the push mirror is blocked by external gate 7.
- [x] External builders can validate, score, compare, and package their own evidence locally.
- [x] Private projection fails closed on unclassified envelope fields, public schema drift, undeclared
  public fields, secret/credential/private-endpoint/local-path/private-identifier field shapes, echoed
  private values, an unbound public digest, and media without a verified-clear publication grant. It
  cannot detect an identifier hidden in free text or media that omits its `media_type`; those remain the
  human review in [publication safety](PUBLICATION.md).
- [ ] v0.1 publishes honest demonstrations with exact capture, cost, rights, and failure receipts.
- [ ] v0.2 publishes frozen blind evidence without train/select leakage.
- [ ] v0.3 proves owner-held improvement, common-ruler non-regression, export, restore, replay, promotion,
  and rollback.
- [ ] v0.4 proves the canonical query, completeness accounting, recipe regeneration, and human authority.
- [ ] The durable site renders only allowlisted source data and records its exact release revision.
- [ ] Every required row is Complete; blocked or deferred work remains incomplete until shipped.

## 8. References

- [Coach-agent authority](COACH_AGENT_AUTHORITY.md)
- [Comparability verdicts](COMPARABILITY.md)
- [Private superset and public projection](PROJECTION.md)
- [Publication safety](PUBLICATION.md)
- [Schema guide](SCHEMAS.md)
- [Media terms](../MEDIA-LICENSE.md)
- [BHI doctrine PR #1063](https://avis-pbook.tail651ec3.ts.net/Khelsutra/badminton-highlight-indexer/pulls/1063)

## 9. Changelog

- 2026-08-27 — Split KE-2 into KE-2a (private superset and public projection) and KE-2b (language-neutral
  contract and portable conformance suite, tracked on issue #2), because the two ship independently and
  only the first is delivered here. KE-2a adds `PrivateEvidenceRecordV1`, the `evidence project`
  command, eight negative fixtures that each refuse for exactly one declared reason, and
  [PROJECTION.md](PROJECTION.md). The projected bytes are canonical, so a published record's SHA-256
  equals the digest its private record declares. Narrowed the private-projection Definition of Done item
  to what the projector actually proves and named the residue as human review; the previous wording
  implied it could find an identifier in free text and unlabelled media, which it cannot. Recorded the
  blocked GitHub backup mirror as external gate 7 with its exact rejection, and split the backup
  Definition of Done item so the verified Actions-disabled half is no longer held hostage by the
  unverified propagation half. Test values that look like credentials are now assembled at run time so
  new commits stop adding push-protection matches; this does not clear the matches already in merged
  history.
- 2026-08-22 — Closed the two non-blocking exact-head review residuals before KE-1 merge: schema
  verification now rejects unresolvable references, and schema-resolution failures at the CLI boundary
  emit structured `error` JSON with exit code 2 instead of a traceback.
- 2026-08-22 — Closed independent-review findings before KE-1 merge: scoring now groups rallies by
  court before deterministic matching; every targeted JSON file is classified and validated or rejected;
  publication rejects unrecognized JSON; official/community registries share `EvidenceRegistryV1`; and
  dependency, error-coordinate, negative-guard, formatting, and deterministic-archive checks are pinned.
- 2026-08-22 — Established the evidence-repository-owned tracker and marked KE-1 `Complete` in the
  proposed post-merge state. Avi created empty `main` commit
  `dd6b437959fa250ccba5afa13c3089430f5530da`; the framework branch was rebased onto that exact head.
  BHI #1063 remains the required doctrine dependency before KE-1 lands, and exact GitHub-backup
  propagation remains a post-merge verification. A clean wheel install exercised validation, scoring,
  comparison, packaging, and synthetic workspace creation. Added Forgejo-native exact-head CI and
  CODEOWNERS routing to Avi; no GitHub Actions workflow was added. Removed age as a proxy for consent
  or publication authority; exact grants remain mandatory.
