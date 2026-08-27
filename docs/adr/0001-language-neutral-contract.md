# ADR-0001: How language-neutral is the v1 evidence contract?

- **Status:** `Proposed` — not accepted. Nothing in this repository may cite this as settled policy.
- **Decider:** Avi Dullu
- **Proposed by:** claude-agent, 2026-08-27
- **Affects:** KE-2b and every later row that asks an outside builder to produce conforming evidence

## Context

The repository ships JSON Schemas, a Python package, and now a portable conformance suite. The schemas
are already implementation-neutral. The behaviour that schemas cannot express — semantic rules,
court-aware scoring, comparability verdicts, canonical digests, publication refusals, deterministic
archives — currently exists only as Python.

That leaves a question the README's promise ("this repository lets builders validate, score, compare,
and package their own evidence") does not answer: must a builder run Python to produce valid evidence,
or only to check it conveniently?

The question is now live rather than theoretical, because KE-5 and KE-6 expect producer repositories to
emit conforming records, and a producer is not obliged to be a Python process.

## Options

### 1. Python-normative

The Python package defines the contract. Any other implementation is correct exactly insofar as it
matches this code, and disagreements are resolved by reading it.

- Cheapest; matches how the repository already works.
- Makes the package a dependency of participation, and a refactor can silently change the contract.
- An outside builder has no way to prove conformance except by running our code on their data.

### 2. Language-neutral contract with a Python reference implementation

The schemas plus `conformance/v1/manifest.json` are normative. Python is one verified route through
them. Behaviour changes require a deliberate suite update, which is visible in review.

- An outside implementation can prove conformance offline, in its own language.
- The suite must be kept honest: it is rendered from the implementation and replayed independently.
- Behaviour not covered by a case is still de facto Python-normative, and the suite must grow to
  cover each new normative behaviour.

### 3. Rewrite the reference implementation in a neutral language now

Move the reference to a language with broader embedding reach, or write a formal specification with no
reference implementation at all.

- Removes any appearance of Python privilege.
- Costs a rewrite before a single outside implementation exists, and a specification with no executable
  reference tends to drift from anything real.

## Proposal

Option 2, and only as a proposal. It is the option that makes conformance checkable today without
spending a rewrite on demand that has not appeared yet.

Under option 2 this repository would say: *Python is a supported verification route, not a prerequisite
for producing valid evidence.* It cannot honestly say that until this ADR is accepted, so no such claim
is made anywhere in the tree yet.

## Consequences if accepted

- Every normative behaviour change must land with a regenerated conformance suite in the same PR.
- Behaviour reachable only through Python and absent from the suite is a gap to close, not a feature.
- The README and `docs/SCHEMAS.md` may then state the language-neutral position directly.

## What would falsify this choice

- No second implementation appears, and the suite becomes maintenance with no reader. Option 1 was then
  the honest answer.
- A second implementation appears and finds the suite underspecifies more than it pins. That argues for
  option 3, or for a much larger suite before any outside builder is invited.
