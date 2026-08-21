# KhelSutra Evidence

An open, local-first framework for publishing and comparing evidence from sports-video systems without
turning a model score into a coaching claim.

> **KhelSutra is an AI agent for the coach. It is never the AI coach.**
>
> **You coach. KhelSutra does the video work.**

This repository lets builders validate, score, compare, and package their own evidence. It treats real
capture conditions, commercialization rights, inference economics, owner-model portability, failures,
and human authority as first-class data—not prose added after a result looks good.

## Current public state

**Framework preview only. There are no official KhelSutra quality releases in this repository yet.**

The checked-in examples are synthetic and exist to exercise the contracts. They are not product evidence,
not a blind benchmark, and not permission to claim that the north-star coach query ships today.

## What is included

- Versioned JSON Schemas for tasks, scenarios, costs, runs, releases, commercialization, owner-model
  adaptation/portability, and coach-agent execution.
- A reference rally-boundary scorer with deterministic one-to-one matching.
- Comparability verdicts with reasons: `paired`, `paired_quality_only`, `partially_comparable`,
  `descriptive_only`, or `incompatible`.
- Fail-closed validation and public-package safety scanning.
- Separate official and community registries.
- Static evidence-site source that can be published only after infrastructure approval.

## Install and run

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/evidence verify examples
.venv/bin/evidence score examples/rallies/truth.json examples/rallies/prediction.json
.venv/bin/evidence compare examples/runs/system-a.json examples/runs/system-b.json
.venv/bin/evidence package examples dist/examples.tar.gz
```

Create a synthetic starter workspace:

```bash
evidence init /tmp/my-evidence
evidence verify /tmp/my-evidence
```

## Evidence doctrine

An official release must expose enough information for an independent reader to understand:

1. what task was run and which samples were included;
2. how many courts and games were visible and active;
3. which observations were human-confirmed, model-produced, calculated, asserted by the coach, or unknown;
4. what failed, was retried, excluded, or manually corrected;
5. the raw cost numerator and source-duration denominator;
6. whether each commercial dependency is verified clear, restricted, unknown, or not applicable;
7. whether an owner adaptation used disjoint held-out data and can be exported, restored, replayed, and
   rolled back; and
8. whether the agent assembled evidence without issuing an unlabeled coaching prescription.

See [comparability](docs/COMPARABILITY.md), [publication safety](docs/PUBLICATION.md),
[coach-agent authority](docs/COACH_AGENT_AUTHORITY.md), and the [schema guide](docs/SCHEMAS.md).

## Reuse and community comparisons

You may run the tooling against your own work and publish a report by sample ID. Community evidence stays
in a distinct registry and does not inherit KhelSutra verification or endorsement. A verdict says whether
two artifacts can be compared under this contract; it does not certify a model, vendor, licence, or
coaching conclusion.

## Licensing

- Code, schemas, documentation, and synthetic fixtures: Apache-2.0; see [LICENSE](LICENSE).
- Evaluation media: governed separately by [MEDIA-LICENSE.md](MEDIA-LICENSE.md). No media is included in
  this preview.
- Model, dataset, checkpoint, API, codec, and output rights remain artifact-specific and must be recorded
  in each release.

## Development

```bash
ruff check .
mypy src
pytest
```

No GitHub Actions workflow is included. Forgejo is authoritative; any GitHub repository is a disabled-
Actions backup.
