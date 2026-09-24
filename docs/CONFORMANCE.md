# Portable conformance suite

`conformance/v1/manifest.json` is a single `ConformanceSuiteV1` document that pins the normative
behaviour of the v1 contract. It carries every input inline, so an implementation in any language can
read one file, run the cases, and compare — without installing this package.

The Python package in this repository is one verified route through that suite. Whether it is also the
*definition* of the contract is an open owner decision recorded in
[ADR-0001](adr/0001-language-neutral-contract.md); until that decision is accepted, treat this suite as
the portable statement of behaviour and the Python implementation as its reference.

## Running it

Each case is `{case_id, operation, title, input, expect}`. A runner dispatches on `operation`, feeds
`input`, and compares against `expect`. There are 33 cases:

| Operation | Cases |
|---|---|
| `validate_document` | 11 |
| `public_safety` | 6 |
| `compare_runs` | 5 |
| `project_record` | 4 |
| `score_rallies` | 3 |
| `package_archive` | 2 |
| `plan_digest` | 1 |
| `recipe_digest` | 1 |

Cases are sorted by `case_id`, and `suite_digest` is the SHA-256 of the canonical JSON encoding of the
`cases` array — sorted keys, no insignificant whitespace. Recompute it before trusting a copy you did
not fetch yourself; `evidence verify conformance/v1/manifest.json` does this for you.

## Operations

- **`validate_document`** — `input.document`; see the normativity rule below.
- **`score_rallies`** — `input.truth`, `input.prediction`, `input.tolerance_frames`; expect
  `result` (a full `RallyScoreV1`) or `error`.
- **`compare_runs`** — `input.left`, `input.right`; expect `result` (a full `ComparisonReportV1`) or
  `error`.
- **`plan_digest`** / **`recipe_digest`** — `input.document`; expect `digest`.
- **`public_safety`** — `input.value`, which may be any JSON value; expect `issues` as rendered
  `path: message` strings.
- **`project_record`** — `input.record`; expect `refusals` as `{reason, path, message}` objects, plus
  `public_record_digest` when `refusals` is empty.
- **`package_archive`** — `input.files` as `{name, text}` pairs; expect `members` and `sha256`, or
  `error`. A refusal names the member and the reason and never a directory, so the expectation does not
  depend on where the runner unpacked the case.

## What is normative, and what is not

`validate_document` reports the layer that rejected a document, because the three layers are not equally
portable:

| `stage` | Meaning | Normative part |
|---|---|---|
| `structural` | missing or unrecognised `schema_name` | `issue_paths` **and** `messages` |
| `schema` | rejected by JSON Schema itself | `issue_paths` only |
| `semantic` | rejected by a rule this repository authors | `issue_paths` **and** `messages` |

Schema-stage wording belongs to whichever JSON Schema library an implementation uses. Requiring a Go or
Rust implementation to reproduce this repository's Python library's English would make the suite
unpassable for everyone but us, which is the opposite of the point. Every other message in the corpus is
authored here and is normative.

## Comparing results

Compare **parsed JSON values**, never serialized text:

- Numbers are IEEE-754 doubles. `0.6666666666666666` in a `result` is the double nearest two thirds, and
  an implementation that computes the same double conforms however it chooses to print it. Comparing
  rendered numerals instead will fail on correct implementations.
- Object key order is not significant anywhere in a case. Array order **is** significant: `matches`,
  `issues`, `messages`, `refusals`, `members`, and the sample-id lists in a comparison report are
  ordered outputs, and `issue_paths` is sorted.
- `null` and absent are different. `stage` is `null` for a passing `validate_document` case, and
  `mean_start_error_frames` is `null` when nothing matched; neither may be dropped.

The one place text equality is required is `suite_digest`, which is computed over the canonical encoding
described above.

## Deliberate omissions

Provider-token shapes — GitHub, Google, Slack, and AWS credential patterns — are exercised in this
repository's own tests but are **not** embedded in the portable corpus. Committing a value that matches a
credential pattern can make push mirrors fail GitHub push protection; this previously blocked this
repository's backup. Implementations should test those patterns against their own scanner; the corpus
covers private endpoints, local paths, signed-URL credentials, and private-only field names instead.

`public_schema_drift` refusals in `project_record` are likewise absent, for the same reason as
schema-stage validation: the refusal reason is ours but the message inside it is the library's.

## Keeping it honest

The suite is rendered from the reference implementation, never written by hand:

```bash
python tools/render_conformance.py
```

`tests/test_conformance.py` fails if the checked-in file differs from what the renderer produces, and
separately replays every case through the public API without touching the renderer, so a renderer bug
cannot make the corpus agree with itself.

## What conformance does not mean

Passing this suite means an implementation reproduces the pinned behaviour on the pinned inputs. It is
not a statement about evidence quality, model quality, rights, or fitness for a coaching claim, and it
does not replace the human review in [publication safety](PUBLICATION.md).
