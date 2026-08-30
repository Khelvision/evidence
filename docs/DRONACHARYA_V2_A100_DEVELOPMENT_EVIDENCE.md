# Dronacharya-v2 A100 development evidence

This note records what the 2026-08-30 Dronacharya-v2 E0 run establishes, what it does not establish,
and which exact producer artifacts carry the result. It is an input to KE-5 planning. It is not a
public evidence release or a completion record for v0.3.

## Run identity

- fresh Qwen3.5-9B R64 LoRA; no prior adapter resume;
- 666 of 666 planned steps completed on A100;
- final-step mean token NLL: 0.1739, used only as a training diagnostic;
- six-clip racket-sport development panel; and
- canonical scoring from locked BHI scorer commit
  `1d58c0a183d6355668fe690f08b34689a52631a8`, recorded by BHI reviewed head
  `71bdcf6a7bc6b41d628f1455958f5ba60f9d03dc`.

The initial fork report used a merge rule that included gaps exactly equal to 1.5 seconds. The canonical
rule uses a strict boundary and keeps those gaps distinct. The following values are the corrected
numbers of record and supersede the initial 0.4640-to-0.6872 macro report.

## Canonical result

| Measure | Baseline C | Adapted D | D − C |
|---|---:|---:|---:|
| Six-clip macro tolF1 | 0.4572 | 0.6800 | +0.2229 |
| Badminton macro tolF1 | — | 0.8885 | — |
| Table-tennis tolF1 | — | 0.5263 | — |
| Pickleball tolF1 at the locked threshold | — | 0.0000 | — |

| Clip | Sport | Adapted D tolF1 |
|---|---|---:|
| `GX010115` | Badminton | 0.9600 |
| `GX010118` | Badminton | 0.7945 |
| `GX010119` | Badminton | 0.8250 |
| `GX020135` | Badminton | 0.9744 |
| `GX020167` | Table tennis | 0.5263 |
| `Pickleball_ELT_2` | Pickleball | 0.0000 |

A development-only threshold sweep raised the pickleball clip to approximately 0.581. That sweep used
the clip to choose its own threshold, so it is diagnostic evidence and must not be quoted as an unbiased
or locked result.

## Claim boundary

The panel is historically reused and adaptive. Four badminton clips appeared in prior H1/H15 work; the
table-tennis and pickleball clips appeared in XS artifacts. The 21,296 training windows were also
approximately 90.9% badminton, 5.6% table tennis, and 3.5% pickleball.

The result therefore supports these statements:

- the E0 adaptation improved the canonical score on this development panel;
- the corrected scorer path is independently reproducible at the identified revisions; and
- sport balance and locked-threshold pickleball performance are the next experimental problems.

It does not support these statements:

- “68% accuracy” as a general product claim;
- production readiness or model promotion;
- sealed, blind, or unseen tri-sport generalization; or
- positive pickleball quality at the locked threshold.

## Relationship to KE-5

KE-5 remains pending. A v0.3 owner-adaptation proof still requires an authorized owner corpus, disjoint
held-out data, common-ruler non-regression, portable export, clean restore, replay, promotion, rollback,
time, and cost.

The next controlled experiment should use a fresh base LoRA, whole-session reshuffling, and sport-first
sampling at 50% badminton, 25% table tennis, and 25% pickleball. The prompt, context, rendering, LoRA
shape, scorer, and locked thresholds should remain fixed so the within-run D-minus-C comparison stays
interpretable. This is an experimental recommendation, not a KE-5 gate change.

## Exact producer evidence

- [sft-factory PR #102](https://avis-pbook.tail651ec3.ts.net/Khelsutra/sft-factory/pulls/102):
  training and replay artifacts.
- [BHI PR #1158](https://avis-pbook.tail651ec3.ts.net/Khelsutra/badminton-highlight-indexer/pulls/1158):
  canonical audit at `71bdcf6a7bc6b41d628f1455958f5ba60f9d03dc`.
- [rally-corpus-vault PR #236](https://avis-pbook.tail651ec3.ts.net/Khelsutra/rally-corpus-vault/pulls/236):
  custody sidecar at reviewed head `222b28052e1d904d2925a29511f110af9652eaeb`, file
  `operations/model-custody/2026-08-30-racket-window-r64-v1/upstream-evidence-v2.json`.
- [sports-data-collector PR #92](https://avis-pbook.tail651ec3.ts.net/Khelsutra/sports-data-collector/pulls/92):
  label-inventory evidence.

Producer repositories retain their private artifacts and operational history. This repository links
their exact revisions without claiming to own or publish those artifacts.
