# Dronacharya-v2 A100 development evidence

This note records what the 2026-08-30 Dronacharya-v2 E0 run establishes, what it does not establish,
and how the result is tied to producer evidence. It is an input to KE-5 planning, not a formal
public evidence release or a completion record for v0.3. Model architecture, adaptation parameters,
training composition, processing recipes, and private operational locators are withheld here.
The producer repositories retain the detailed record; this note is not a public reproduction bundle.

Earlier versions of this note were publicly readable. Redacting the current version does not retract
Git history or copies already distributed.

## Run identity

- a fresh adaptation run completed on A100 without resuming a prior adapter;
- final-step mean token NLL: 0.1739, used only as a training diagnostic;
- six-clip racket-sport development panel; and
- canonical scoring from locked BHI scorer commit
  `1d58c0a183d6355668fe690f08b34689a52631a8`, recorded by BHI reviewed head
  `71bdcf6a7bc6b41d628f1455958f5ba60f9d03dc`.

The initial fork report used a noncanonical scoring interpretation. The locked producer scorer
corrected that interpretation. The following values are the corrected numbers of record and
supersede the initial 0.4640-to-0.6872 macro report; the private scorer record carries the exact rule.

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
table-tennis and pickleball clips appeared in XS artifacts. The training mix was dominated by
badminton, with smaller table-tennis and pickleball representation. That imbalance remains a
material limitation; the exact composition belongs to the private producer record.

The result therefore supports these statements:

- the E0 adaptation improved the canonical score on this development panel;
- the corrected scores are tied to locked producer revisions, with reproduction requiring access
  to the private implementation and inputs; and
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

The next controlled experiment should address sport imbalance while holding the comparison
conditions fixed so the within-run D-minus-C result stays interpretable. Sampling weights, prompts,
context settings, adaptation shape, rendering, scorer rules, and thresholds remain in the private
experiment plan. This is an experimental recommendation, not a KE-5 gate change.

## Producer evidence and custody boundary

The private producer record identifies training/replay evidence, the canonical scorer audit,
model custody and checkpoint registration, and the label inventory. The canonical scorer revisions
above remain identifiers for that audit; access to those repositories and artifacts is separate
from access to this public note. Private service URLs, model registry locators, and operational
paths are withheld here.

The follow-up custody checks reported verified model identity and a verified stored replica.
Those receipts establish identity and custody only. They grant no model usage, training,
redistribution, production promotion, or serving-default authority. This note publishes neither
model weights nor a grant to use them.
