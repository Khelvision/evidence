# Private superset and public projection

A producer holds more than it may publish. This repository does not ask a producer to redact by hand;
it defines the private record as a **superset envelope** and the public record as its **deterministic
projection**.

`PrivateEvidenceRecordV1` carries exactly three kinds of material, and the envelope is closed, so every
field must be one of them:

- `public` — exactly one public evidence document, projected verbatim;
- `private_extensions` — producer material that is never projected;
- `producer`, `media_authorizations`, `projection` — the authority and binding that permit publication.

An unclassified sibling field is not silently dropped. It fails the envelope contract, because a field
nobody classified is a field nobody reviewed.

## Running it

```bash
evidence project private-examples/private-evidence-record.json --output dist/public.json
evidence project private-examples/private-evidence-record.json | sha256sum
```

Standard output carries the public record and nothing else, so the command composes. Refusals go to
standard error as `{"status": "refused", "refusals": [...]}` with exit status 1; malformed input exits 2.

The projected bytes are canonical JSON — sorted keys, no insignificant whitespace, no trailing newline —
so the published file's SHA-256 equals `projection.public_record_digest.value`. A reader who has the
public file can confirm it is exactly the record the producer bound, and a producer who edits the public
payload without re-binding the digest is refused rather than published.

## Refusal reasons

| Reason | Refused when |
|---|---|
| `envelope_invalid` | the record is not a valid `PrivateEvidenceRecordV1`, including any unclassified field |
| `public_schema_drift` | the public payload fails its own v1 contract or semantic rules, including undeclared fields |
| `unsafe_public_value` | a projected value carries a secret, credential, private endpoint, local path, or private identifier |
| `unauthorized_media` | published media has no authorization, no `verified_clear` publication grant, or no granted `public_evidence` purpose |
| `dead_media_authorization` | an authorization names an artifact the projection never references |
| `private_value_echo` | a `private_extensions` value of 12 characters or more reappears inside the projection |
| `projection_digest_mismatch` | the declared public digest does not bind the projected bytes |

Every reason is reported, not just the first, so a producer sees the whole gap in one pass.

`private_value_echo` treats overlap as an error in classification rather than a formatting accident: a
value that belongs in public evidence is not a private extension, and a private extension that must be
published belongs in `public`.

## Media authority

Each authorization binds one artifact to its exact consent, any guardian or legal authorization,
its purpose grants, its custody, and its publication grant. Participant age is not a field here and is
never a proxy for permission; the grants are.

## What this does not prove

The projector classifies media from the `media_type` declared on an artifact reference. A reference that
omits `media_type` is not treated as media, so the tool cannot discover unlabelled media on its own.
It also cannot judge whether a consent document says what a producer claims it says.

Publication of real media therefore still requires the human review in [publication safety](PUBLICATION.md).
A clean projection means the record is publishable under this contract. It is not a rights opinion, and it
is not evidence quality.

## Producer boundary

Producer repositories own their private receipts, their storage, and their CI. This repository owns the
envelope contract, the projector, and the refusal semantics. A producer integration is a dependency
recorded in [the tracker](PROJECT.md), not work completed here.
