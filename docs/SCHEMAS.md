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
active games not exceeding visible courts, recomputed cost rates matching their raw values, blind releases
not being marked exposed before freeze, held-out inventories being disjoint from training, and coach-agent
authority flags remaining human-controlled.
