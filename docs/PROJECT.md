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
  and multiple active games. They are exposed examples, never blind evidence. **Owner decision,
  2026-08-27: v0.1 is `evidence_only`** — it publishes measurements derived from the footage and not the
  footage, so it cannot be independently re-scored and says so in `ReleaseDistributionV1` rather than in
  prose. The owner holds the rights either way; this is a scope choice, not a rights limitation, and the
  declaration carries an upgrade path to `media_included`.
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
| KE-2a | Publish the private-superset/public-projection contract, the projector, and negative fixtures; producer integrations remain in their own repositories | KE-1 | Security review of the envelope classification, refusal reasons, and negative fixtures | Complete | [#3](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/pulls/3) |
| KE-2b | Publish the portable conformance suite that pins normative behaviour, and propose the normativity decision as an ADR | KE-2a | Conformance corpus rendered from the implementation, replayed independently by the Python tests, and free of expectations only Python can meet | Complete | [#4](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/pulls/4) |
| KE-3 | Publish the v0.1 demonstration release | KE-1, KE-2a, KE-9, KE-10 | `evidence media-preflight` clears every sample under the declared distribution, plus redaction and claims review | Blocked | — |
| KE-4 | Publish the frozen v0.2 blind challenge | KE-3 | Rights-cleared frozen inventory, two annotators, frozen scorer/engine, no train/select overlap | Pending | — |
| KE-5 | Publish the v0.3 owner-adaptation and portability proof | KE-2a | Authorized owner corpus, disjoint held-out ruler, and second clean environment | Pending | — |
| KE-6 | Publish the v0.4 coach-agent query proof | KE-2a | Governed player/match/outcome/shot metadata and deterministic recipe renderer | Pending | — |
| KE-7a | Make the site source-driven: render the release index as an allowlisted projection of the registries, refuse what it may not publish, and stamp the exact release data it rendered | KE-1 | Checked-in page byte-identical to the renderer; refusals covered by tests | Complete | [#6](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/pulls/6) |
| KE-7b | Deploy the durable evidence site | KE-7a | Explicit infrastructure/domain approval and a source-driven deployment path | Pending | — |
| KE-8 | Publish a worked end-to-end walkthrough for outside builders, executed by CI | KE-2a | Every command runs in the test suite and every documented output is checked against real output | Complete | [#5](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/pulls/5) |
| KE-9 | Publish the media-grant contract and the publication preflight, so KE-3's rights gate is mechanical rather than a judgement made at publication time | KE-1 | Every blocking requirement covered by a fixture that withholds exactly one thing | Complete | [#8](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/pulls/8) |
| KE-10 | Publish the release-distribution contract so a release states whether it hands over its footage, and gate the preflight on it | KE-9 | Evidence-only relaxes exactly one requirement and the report names it | Complete | — |

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
7. ADR-0001 is `Proposed`, not accepted. Until Avi decides, this repository does not claim that the
   contract is defined language-neutrally; it claims only that a portable suite pins the behaviour.
   Tracked on [issue #2](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/issues/2).
8. The Forgejo-to-GitHub backup mirror is failing and needs an owner decision on GitHub. Every scheduled
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
  GitHub still has zero branches; the push mirror is blocked by external gate 8.
- [x] External builders can validate, score, compare, and package their own evidence locally.
- [x] A worked walkthrough takes an outside builder from an empty directory to a packaged public
  archive, including a real refusal. CI executes every command in it and checks every documented output
  against what the command actually printed, so the walkthrough cannot drift into a claim the tool does
  not support.
- [x] Private projection fails closed on unclassified envelope fields, public schema drift, undeclared
  public fields, secret/credential/private-endpoint/local-path/private-identifier field shapes, echoed
  private values, an unbound public digest, and media without a verified-clear publication grant. It
  cannot detect an identifier hidden in free text or media that omits its `media_type`; those remain the
  human review in [publication safety](PUBLICATION.md).
- [x] A portable conformance suite pins the contract's normative behaviour in one file: 33 cases across
  document validation, court-aware scoring, comparability verdicts, canonical digests, public-safety
  scanning, projection refusals, and deterministic archives. It is rendered from the reference
  implementation and replayed independently, and it records which expectations are normative and which
  belong to whichever JSON Schema library ran. Whether the contract is *defined* language-neutrally is
  external gate 7 and is not claimed here.
- [x] The rights gate on a media release is mechanical: `MediaGrantV1` records the rights position for
  one sample without recording who anyone is, and `evidence media-preflight` reports per sample whether
  publication, venue permission, participant consent for the `public_evidence` purpose, guardian
  authorization where required, and non-withdrawal are all in place. Clearing publication does not imply
  training or rehosting, and no green preflight is a legal opinion.
- [ ] v0.1 publishes honest demonstrations with exact capture, cost, rights, and failure receipts.
- [ ] v0.2 publishes frozen blind evidence without train/select leakage.
- [ ] v0.3 proves owner-held improvement, common-ruler non-regression, export, restore, replay, promotion,
  and rollback.
- [ ] v0.4 proves the canonical query, completeness accounting, recipe regeneration, and human authority.
- [x] The site source renders its release index only from an allowlisted projection of the registries.
  It refuses an unallowlisted field, an unsafe value, or a registry that fails its own contract; it
  escapes registry data so it cannot become markup; and it stamps the SHA-256 of the exact projection it
  rendered. CI fails if the checked-in page drifts from that projection. The page no longer asserts its
  own emptiness in prose beside the data.
- [ ] No durable site is deployed and no domain is claimed. Publication remains external gate 6.
- [ ] Every required row is Complete; blocked or deferred work remains incomplete until shipped.

## 8. References

- [Site source](SITE.md)
- [Walkthrough](WALKTHROUGH.md)
- [Coach-agent authority](COACH_AGENT_AUTHORITY.md)
- [Comparability verdicts](COMPARABILITY.md)
- [ADR-0001: how language-neutral is the contract](adr/0001-language-neutral-contract.md)
- [Conformance suite](CONFORMANCE.md)
- [Media grants, distribution modes, and the publication preflight](MEDIA_GRANTS.md)
- [Private superset and public projection](PROJECTION.md)
- [Publication safety](PUBLICATION.md)
- [Schema guide](SCHEMAS.md)
- [Media terms](../MEDIA-LICENSE.md)
- [BHI doctrine PR #1063](https://avis-pbook.tail651ec3.ts.net/Khelsutra/badminton-highlight-indexer/pulls/1063)

## 9. Changelog

- 2026-08-27 — KE-10 adds `ReleaseDistributionV1` and teaches the preflight about it, recording the owner
  decision that v0.1 is `evidence_only`. A release now states machine-readably whether it hands over its
  source media, and an evidence-only declaration may not claim `independent_rescoring_possible` and must
  name what it withholds — the central limitation of publishing this way, enforced rather than
  footnoted. Evidence-only relaxes exactly one preflight requirement, the media publication grant,
  because a release that hands over no footage does not exercise the right to publish it; consent,
  guardian authorization, withdrawal, and venue permission all still block, since the people in the
  footage are still being measured in public. The report names `relaxed_requirements`, so a green result
  never hides which check was skipped, and a release with no declaration is read as handing over media.
  `EvidenceReleaseV1` is untouched: a released schema is immutable, so the new fact took a new contract
  rather than a field on an old one.
- 2026-08-27 — KE-9 adds `MediaGrantV1` and `evidence media-preflight`, turning KE-3's rights gate from a
  judgement made at publication time into a per-sample checklist. A grant records the rights position for
  one sample — publication grant, venue permission, copyright holder, custody, per-participant consent by
  purpose, guardian authorization where required — and deliberately records no name, age, or contact
  detail: participants are opaque within-sample handles bound to consent documents by digest, because a
  rights register that becomes a participant register has made things worse. Six fixtures each withhold
  exactly one requirement. The report states separately whether a grant permits training and rehosting,
  since clearing publication implies neither and `MEDIA-LICENSE.md` prohibits both by default. KE-3 stays
  Blocked; what changed is that its gate is now something a tool can answer.
- 2026-08-27 — Added section 10, merge receipts: the reviewed head, merge commit, and exact-head CI run
  for every merged row, with the time each turned green next to the time it was merged. KE-8 and KE-7a
  were merged before their gate completed, by 2m05s and 2m59s; both heads then verified green, so the
  record is that the gate was skipped rather than that anything shipped broken. The two red runs on
  KE-2b's head are annotated as runner-host disk contention, since a red board that reached no gate step
  says nothing about the diff.
- 2026-08-27 — KE-7a makes the site source-driven and splits deployment out as KE-7b. The release index
  in `site/index.html` is now a deterministic allowlisted projection of the registries rendered by
  `tools/render_site.py`, ending in the SHA-256 of exactly that projection; `tests/test_site.py` fails if
  the checked-in page drifts from it. The renderer refuses an unallowlisted release or digest field, a
  value that fails the public-safety scan, and a registry that fails its contract or declares the wrong
  discriminator, and it escapes registry data so markup in a release id cannot become markup on the page.
  The hand-typed sentence "there are no official KhelSutra quality releases yet" was removed: the first
  registry entry would have made it false with nothing to notice, and the page now says the registries
  are empty because they are. Deployment is unchanged and still needs external gate 6.
- 2026-08-27 — KE-8 adds [WALKTHROUGH.md](WALKTHROUGH.md): one builder taking a single evening session
  from an empty directory to a packaged public archive, through scoring that withholds credit for a
  rally found on the wrong court, a `paired_quality_only` verdict that says exactly how far the
  comparison carries, and a projection refused for a staging path left in the notes.
  `tests/test_walkthrough.py` executes every command block in file order and requires each documented
  output to be a subset of what the command really printed, so the walkthrough may abridge an output
  but may not invent one. That check caught an invented digest in the first draft.
- 2026-08-27 — KE-2b publishes `conformance/v1/manifest.json`, a single `ConformanceSuiteV1` document
  with 33 inline cases across eight operations, plus [CONFORMANCE.md](CONFORMANCE.md) and
  [ADR-0001](adr/0001-language-neutral-contract.md). The suite is rendered by
  `tools/render_conformance.py` from the reference implementation and replayed by the tests through the
  public API without the renderer, so neither side can agree with itself. `validate_document` cases
  record which layer rejected a document: `structural` and `semantic` messages are authored here and
  bind, while `schema` cases bind only their issue paths, because requiring another language's JSON
  Schema library to reproduce this one's English would make the suite unpassable for everyone but us.
  Provider-token shapes are deliberately excluded from the corpus and stay in the Python tests, because
  committing a credential-shaped literal is what blocked the GitHub backup in the first place. The
  KE-2b gate was rewritten: the normativity decision is an owner call, so ADR-0001 ships `Proposed` as
  external gate 7 and the row is complete on the suite alone. No claim that the contract is defined
  language-neutrally appears anywhere in the tree.
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

## 10. Merge receipts

The merge gate is exact-head terminal-green CI: the reviewed head must be green before Avi merges it.
This table records what actually happened for every merged row, including where the gate was met only
after the merge. Times are IST.

| Row | PR | Reviewed head | Merge commit | Exact-head CI | Green | Merged | Gate met first |
|---|---|---|---|---|---|---|---|
| KE-1 | #1 | `f04634a` | `e467f03` | [run 4](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/actions/runs/4) success | 2026-08-22 18:35 | 2026-08-22 22:21 | yes |
| KE-2a | #3 | `391be05` | `dc092b0` | [run 7](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/actions/runs/7) success | 07:28:26 | 07:46:20 | yes |
| KE-2b | #4 | `d38fed6` | `7986788` | [run 13](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/actions/runs/13) success | 09:10:16 | 12:22:22 | yes |
| KE-8 | #5 | `d13202c` | `f04a78e` | [run 17](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/actions/runs/17) success | 12:27:30 | 12:25:25 | **no — green 2m05s after** |
| KE-7a | #6 | `be6f30b` | `82e3f02` | [run 20](https://avis-pbook.tail651ec3.ts.net/Khelsutra/evidence/actions/runs/20) success | 12:37:10 | 12:34:11 | **no — green 2m59s after** |

Every reviewed head in this table verified green, and each had passed the full local gate before its
pull request opened, so no merged tree is in question. What the two `no` rows record is that the gate
was not consulted, which is a different fact and worth keeping: a green board read afterwards cannot
tell you whether it was green at the moment someone pressed merge.

Runs 4105 and 4107 on `d38fed6` are red and are not defects. Both died inside `pip install` with
`context deadline exceeded` against the Docker socket, reaching no gate step, while three heavyweight
containers from another repository were resident on the runner host — io `full avg10` 7.33 rising to
20.14 against cpu `full avg10` 0.00. The same head passed in 30 s once that eased. A red board on this
repository is worth reading before it is believed.
