# How a system's output was produced

A rally-boundary score of 0.90 means one thing when a model produced it and something else when a
person watched the video and typed the boundaries. Both numbers can be correct. Putting them on one
axis is often the interesting comparison — but doing it silently is the kind of claim this framework
exists to prevent.

`SystemProvenanceV1` binds one `run_id` to how its output was made:

| `operation_mode` | Meaning |
|---|---|
| `automated` | no human produced any part of the output |
| `human_in_the_loop` | a model produced it and a person corrected it |
| `human_produced` | a person produced it |
| `undisclosed` | nobody has said |

A human mode must state `human_minutes_per_source_hour`. That number, not the label, is what makes two
systems commensurable: it is the difference between a result that scales and a result that is somebody's
afternoon. An `automated` run may not bill human minutes.

## Saying how you know

`disclosure_basis` is the field that keeps this honest:

| Basis | Meaning | Receipt required |
|---|---|---|
| `vendor_stated` | the vendor said so | yes |
| `observed` | you watched it happen | yes |
| `inferred` | you concluded it from behaviour | no |
| `unknown` | you do not know | no — and the mode must be `undisclosed` |

Repeating what a vendor published about their own product is not the same act as concluding something
about them yourself. The contract makes you say which, and binds a document to the first two.

## Publication

`evidence package` refuses any `SystemProvenanceV1` whose basis is not `vendor_stated`. A conclusion you
reached about somebody else's product is a competitive claim: it may be true, it may be well evidenced,
and it still does not belong in a public evidence package. Competitive positioning has its own home and
its own review rules.

Your own runs are the case this contract most wants filled in. "Automated, vendor stated, zero human
minutes, here is the receipt" is a disclosure about yourself, and it is publishable precisely because it
is checkable against you.

## In a comparison

`evidence compare left.json right.json --provenance <dir>` adds a reason naming both modes, or naming
which side is undisclosed. It does **not** change the verdict. Comparing a model to a person is a real
comparison and the framework will not refuse it — it will only refuse to let it happen quietly.

With nothing declared, every comparison says so:

> operation mode is undisclosed for both runs; a number produced by a model and one produced by a
> person are different claims

## What this cannot do

It cannot detect how a system works. Every value here is asserted by whoever wrote the document, and the
`disclosure_basis` field exists because that assertion has a provenance of its own. A system that
describes itself as automated and is not will pass this contract and fail a field test.
