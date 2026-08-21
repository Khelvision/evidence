# Schema guide

Schemas use JSON Schema Draft 2020-12 and stable `urn:khelsutra:evidence:*` identifiers. Every document
contains `schema_name`, `schema_version`, and `record_id`.

The v1 contracts are grouped into:

- task/scenario/system evidence;
- commercialization and cost;
- release and comparison;
- owner workspace, model package, adaptation, and portability; and
- coach instruction, evidence recipe, and agent-run receipt.

`RallyBoundarySetV1` and `RallyScoreV1` are reference-scoring transport contracts used by the CLI.

Schema validation is necessary but not sufficient. The verifier also enforces semantic rules such as
active games not exceeding visible courts, per-court rally overlap rules, recomputed cost rates matching
their raw values, all nine commercialization categories being present exactly once, blind releases not
being marked exposed before freeze, held-out inventories being disjoint from training, and coach-agent
authority flags remaining human-controlled.

Coach plans and reel recipes carry canonical SHA-256 identities. A recipe binds every source through an
artifact digest, so regenerability does not depend on an ambiguous filename. Portability receipts require
a clean second environment plus content-addressed export, restore, reproduction, promotion, and rollback
evidence.
