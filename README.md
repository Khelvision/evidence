# KhelVision Evidence

An open, local-first framework for publishing and comparing evidence from sports-video systems without
turning a model score into a coaching claim.

KhelSutra is the research, evidence, and open-tooling organization behind the
[KhelVision product](https://khelvision.com/). Explore the
[evidence site and release index](https://evidence.khelsutra.guru/) or the
[Android app page](https://khelvision.com/android). This public repository lives at
[Khelvision/evidence](https://github.com/Khelvision/evidence). The existing
`khelsutra-evidence` package, `khelsutra_evidence` import, and `urn:khelsutra:evidence:*` schema IDs are
stable contract names; the GitHub organization move does not change them.

> **KhelVision helps the coach inspect video. It is never the AI coach.**
>
> **You coach. KhelVision does the video work.**

This repository lets builders validate, score, compare, and package their own evidence. It treats real
capture conditions, commercialization rights, inference economics, owner-model portability, failures,
and human authority as first-class data—not prose added after a result looks good.

## Current public state

**Framework preview only.** The [release index](https://evidence.khelsutra.guru/#release-index)
shows the current official and community registry state; the live page is a manual deployment, so check
the [source registries](registry/) when publication freshness matters.

The checked-in examples are synthetic and exist to exercise the contracts. They are not product evidence,
not a blind benchmark, and not permission to claim that the north-star coach query ships today.

Delivery status, repository boundaries, gates, and release rows live in the
[canonical project tracker](docs/PROJECT.md). Producer repositories own their private receipt and
integration work; this repository owns the public contracts, tooling, registries, release manifests, and
site source.

## What is included

- Versioned JSON Schemas for tasks, scenarios, costs, runs, releases, commercialization, owner-model
  adaptation/portability, and coach-agent execution.
- A reference rally-boundary scorer with deterministic, court-aware one-to-one matching.
- Comparability verdicts with reasons: `paired`, `paired_quality_only`, `partially_comparable`,
  `descriptive_only`, or `incompatible`.
- Fail-closed validation, a private-superset-to-public projector, a media-grant preflight, and
  public-package safety scanning.
- Content-addressed coach plans, source-bound reel recipes, and clean-environment portability receipts.
- Operation-mode disclosure, so a model's score and a person's score are never silently compared.
- A portable conformance suite that pins the contract's normative behaviour in one file.
- Separate official and community registries.
- Static evidence-site source whose release index is generated from the registries, not typed
  beside them. The public Cloudflare Pages site is currently deployed manually; source-driven
  deployment remains open as KE-7b in the [tracker](docs/PROJECT.md).

## Install and run

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/evidence verify examples
.venv/bin/evidence score examples/rallies/truth.json examples/rallies/prediction.json
.venv/bin/evidence compare examples/runs/system-a.json examples/runs/system-b.json
.venv/bin/evidence project private-examples/private-evidence-record.json --output dist/public.json
.venv/bin/evidence media-preflight examples/evidence-release.json private-examples \
  --distribution examples/release-distribution.json
.venv/bin/evidence package examples dist/examples.tar.gz
```

`evidence project` turns a private record into the exact public bytes it authorizes, and refuses rather
than redacts. The published file's SHA-256 equals the digest the private record declares.

New here? The [walkthrough](docs/WALKTHROUGH.md) takes one builder from an empty directory to a
packaged public archive, refusals included.

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
[private superset and public projection](docs/PROJECTION.md),
[media grants](docs/MEDIA_GRANTS.md), [coach-agent authority](docs/COACH_AGENT_AUTHORITY.md),
the [conformance suite](docs/CONFORMANCE.md), and the [schema guide](docs/SCHEMAS.md).

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
python tools/render_conformance.py   # after a deliberate behaviour change
```

Forgejo runs the same lint, type, full-suite coverage, wheel, and clean-install gates from
[`.forgejo/workflows/ci.yml`](.forgejo/workflows/ci.yml). No GitHub Actions workflow is included.
Forgejo is authoritative; [Khelvision/evidence](https://github.com/Khelvision/evidence) is the
public GitHub backup with Actions disabled.
