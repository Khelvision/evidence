# Media grants and the publication preflight

A release names sample IDs. Behind each of those is footage of real people in a real venue, and the
right to publish it exists only as a set of documents somebody obtained. `MediaGrantV1` records that
rights position, and `evidence media-preflight` compares it against a proposed release.

```bash
evidence media-preflight release.json grants/ [--distribution distribution.json]
```

Exit 0 when every sample in the release is cleared, 1 when any is not, 2 on malformed input. The report
names, per sample, exactly what is missing — so "get the media grants" becomes a checklist instead of a
judgement made at publication time.

## Two ways to publish, and only one of them hands over footage

A release that publishes measurements derived from footage is a different artifact from one that
publishes the footage too, and `ReleaseDistributionV1` makes a reader able to tell which they hold
without being told in prose.

| `distribution` | What a reader gets | What the preflight requires |
|---|---|---|
| `media_included` | the evidence and the source media | every requirement below |
| `evidence_only` | the evidence, keyed by sample ID | every requirement **except** the media publication grant |

`evidence_only` relaxes exactly one thing: a release that hands over no footage does not exercise the
right to publish that footage. Everything about the people in it still applies — they are still being
measured in public, and consent, guardian authorization, and withdrawal all still block. The report
names `relaxed_requirements` explicitly, so a green result never hides which check was skipped.

Without a `--distribution` document the strictest reading applies and the release is read as handing
over media. Publishing less than that is a claim somebody has to put on the record.

An `evidence_only` declaration may not claim `independent_rescoring_possible`, and must name what it
withholds. Both are enforced, because "you cannot re-run our scorer against the original video" is the
central limitation of publishing this way and should not be left to a footnote.

## The grant records rights, not people

A grant carries no name, no age, no contact detail. Participants appear as opaque within-sample handles
(`p1`, `p2`) bound to consent documents by digest. Any mapping from a handle to a person lives outside
this contract, in the custodian's own records.

That is deliberate. A document listing who appears in which footage is itself the sensitive artifact,
and this framework's own scanner treats participant identifiers as unpublishable. A rights register that
becomes a participant register has made things worse, not better.

`MediaGrantV1` is a private contract. It belongs with the producer's receipts, not in a public package.

## What blocks a sample

| Requirement | Blocked when |
|---|---|
| `publication_not_verified_clear` | the publication grant is restricted, unknown, or not applicable |
| `venue_permission_unresolved` | venue permission is restricted or unknown |
| `no_participants_recorded` | the grant lists no participant at all |
| `participant_consent_missing_public_evidence` | a participant's consent does not grant the `public_evidence` purpose |
| `guardian_authorization_missing` | a participant needs guardian or legal authorization and none is bound |
| `participant_withdrawn` | a participant withdrew |

Every gap is reported at once, per sample, so one pass tells you the whole shape of the work.

`no_participants_recorded` is not a technicality. Footage containing nobody and footage nobody reviewed
are indistinguishable to a tool, so the preflight refuses to guess which it is looking at.

## Consent is per purpose, and publication is not the only purpose

`purpose_grants` uses the same purposes as the rest of the framework: `service_operation`,
`owner_model_improvement`, `shared_model_improvement`, `research`, `public_evidence`, `marketing`. A
participant who agreed to their video being processed has granted `service_operation`. That is not
consent to publish, and the preflight will not treat it as such.

Age is not a field here. Per the programme's locked contracts, age alone neither grants nor denies a
use; the grant does. `guardian_authorization_required` is the custodian's assertion that some authority
beyond the participant's own consent is needed, and binding that authorization is then mandatory.

## Clearing publication clears only publication

The report states, per sample, whether the grant permits `training` and `rehosting`. Neither is required
to publish, and neither is implied by publishing. `MEDIA-LICENSE.md` defaults both to prohibited unless a
release-specific grant says otherwise, and a cleared preflight does not change that default.

## What this cannot do

It cannot read a consent document, and it cannot tell you whether one says what its holder believes it
says. It checks that a grant exists, is bound by digest, and covers the purpose being exercised. Whether
the underlying paperwork is sound remains the human review in [publication safety](PUBLICATION.md), and
no green preflight is a legal opinion.
