# Alternative annotation sources

An alternative annotation source is useful because disagreement exposes ambiguity and scorer failure.
It is dangerous when “another set of labels” silently becomes “the truth.” This design keeps those two
facts separate.

## Authority model

- **Primary truth** is the owner-governed canonical label set selected under the producer repository's
  split, rights, and usage rules.
- **Alternative source** is a separately produced annotation of some or all of the same media. It is a
  system output to measure, not an authority to merge automatically.
- **Consensus or adjudication** is a new owner-approved artifact. It must cite both inputs and the human
  decision that resolved each disagreement; a majority vote is not a provenance chain.

An alternative source never changes train/select/holdout eligibility. Licensing and permitted use are
separate from technical comparability. `unknown` or `restricted` permission blocks ingestion even when
the user owns the source video.

## 2026-08-30 authenticated GGAB pass

Private mailbox and authenticated UI evidence confirm a USD 11 GGAB Beta pass on three owner-uploaded
matches. The editor exposed 104 rallies and 456 shots in total:

| Clip | GGAB coverage observed | Existing KhelSutra owner-golden scope | Honest relationship |
|---|---:|---:|---|
| `GX010164` | 39 rallies, 159 shots, through 536.47 s | 74 rallies | partial alternative |
| `GX010165` | 28 rallies, 113 shots, through 379.78 s | 71 rallies | partial alternative |
| `GX010166` | 37 rallies, 184 shots | 38 rallies | near-full alternative |

The GGAB rows report `source=user`, but that application field does not prove whether the output was
automated, human-in-the-loop, or human-produced. Under `SystemProvenanceV1`, the operation mode remains
`undisclosed` with disclosure basis `unknown` unless GGAB makes a checkable statement.

No real GGAB label rows belong in this public repository. The authenticated counts are planning evidence,
not a public vendor-quality result.

## Permission gate

[GGAB's Terms of Service](https://app.getgoodatbadminton.com/terms), last updated 2026-08-18, say the
user retains ownership of uploaded match data and annotations. The same terms prohibit bulk extraction
and using the service to build a competing product without written consent. The ownership clause does
not override that use restriction.

Therefore:

- do not ingest GGAB labels into BHI, train or adapt a model from them, tune a scorer from them, or
  publish a vendor comparison without written permission for the exact use;
- an account/data export is custody, not automatically an evaluation or model-improvement license; and
- internal evaluation, model improvement, public aggregate metrics, redistribution, and naming the
  vendor are distinct permissions.

## KE-13 contract shape

The future contract should be exercised entirely with synthetic examples until a real source clears its
permission gate. A record needs, at minimum:

- immutable source/run identity and artifact digest;
- `operation_mode`, `disclosure_basis`, and receipt where required by `SystemProvenanceV1`;
- producer, annotation specification, timebase, and taxonomy version;
- exact coverage intervals plus source-duration coverage ratio;
- relationship to the primary truth (`alternative`, `adjudicated`, never implicit `canonical`);
- rights/licensing state and separate flags for evaluation, model improvement, redistribution, and
  public comparison; and
- cost and turnaround without inventing a per-clip allocation from a subscription total.

The public packager must refuse real alternative-source records whose permission is not
`verified_clear`, whose basis is an inference about another vendor, or whose values expose private match
data.

## Scoring strategy

1. Freeze the primary labels and the alternative labels independently.
2. Compare only the intersection of their declared coverage. Report full-source and shared-window
   coverage so a partial first game cannot masquerade as a complete match.
3. Report exact start/end deltas and tolerance curves, then classify split, merge, missing, extra, and
   ordering errors. One aggregate F1 is not enough to improve a scorer.
4. Keep outcome and shot-taxonomy disagreement separate from rally-boundary disagreement.
5. Route high-value disagreements to human adjudication. Do not auto-rewrite the primary key or tune a
   production threshold from one vendor's output.
6. Treat the alternative as another system run when benchmarking KhelSutra. A human or undisclosed
   source may be informative, but it is not an automated-product accuracy claim.

If written consent never arrives, this design still applies to an independent annotator engaged under an
explicit evaluation/model-improvement agreement. The USD 11 GGAB pass then remains market research, not
corpus inventory.
