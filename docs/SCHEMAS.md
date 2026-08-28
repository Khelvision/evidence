# Schema guide

Schemas use JSON Schema Draft 2020-12 and stable `urn:khelsutra:evidence:*` identifiers. Every document
contains `schema_name`, `schema_version`, and `record_id`.

The v1 contracts are grouped into:

- task/scenario/system evidence;
- commercialization and cost;
- release, official/community registry, and comparison;
- owner workspace, model package, adaptation, and portability;
- coach instruction, evidence recipe, and agent-run receipt;
- the private superset envelope that projects into a public record;
- the media grant that records whether footage may be published;
- the release distribution that records whether footage is actually handed over; and
- the conformance suite that pins normative behaviour.

`PrivateEvidenceRecordV1` is the only contract a producer holds privately. It wraps exactly one public
document plus the private material and media authority behind it; see
[private superset and public projection](PROJECTION.md). `evidence verify` asks whether a record is
well formed, so a well-formed record that may not be published still verifies; `evidence project` is
where publishability is decided.

`MediaGrantV1` is private like `PrivateEvidenceRecordV1`, and carries no name, age, or contact
detail: participants are opaque within-sample handles bound to consent documents by digest, so a rights
register never becomes a participant register. See [media grants](MEDIA_GRANTS.md).

`ConformanceSuiteV1` is a corpus rather than evidence. It carries documents inline as test data,
including deliberately invalid ones, so provenance rules apply to an embedded document when a runner
validates it and not to the corpus that quotes it. Its `suite_digest` is checked during verification, so
`evidence verify conformance/v1/manifest.json` proves the corpus is intact. See
[the conformance suite](CONFORMANCE.md).

`RallyBoundarySetV1` and `RallyScoreV1` are reference-scoring transport contracts used by the CLI.
`EvidenceRegistryV1` gives the official and community release indexes one validated shape with an
explicit registry discriminator.

Schema validation is necessary but not sufficient. The verifier also enforces semantic rules such as
active games not exceeding visible courts, per-court rally overlap rules, recomputed cost rates matching
their raw values, all nine commercialization categories being present exactly once, blind releases not
being marked exposed before freeze, held-out inventories being disjoint from training, and coach-agent
authority flags remaining human-controlled.

Coach plans and reel recipes carry canonical SHA-256 identities. A recipe binds every source through an
artifact digest, so regenerability does not depend on an ambiguous filename. Portability receipts require
a clean second environment plus content-addressed export, restore, reproduction, promotion, and rollback
evidence.

`evidence verify` examines every JSON file under the requested path except explicit VCS, virtual-
environment, dependency, and tool-cache directories. Evidence instances must declare a known
`schema_name`; JSON Schema documents must declare Draft 2020-12 plus a string `$id`. Unrecognized JSON
fails closed instead of being silently omitted from a successful count. Every `$ref` and `$dynamicRef`
in a schema is resolved against the packaged registry during verification; a missing resource, anchor,
or JSON Pointer is an invalid schema rather than a green result.
