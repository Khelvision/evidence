# Walkthrough: publishing evidence for your own detector

You built a rally detector. You ran it on one evening session in a three-court hall, and you want to
publish what it did — honestly enough that another builder can compare against you, and safely enough
that you have not leaked anything.

This walkthrough is executed by this repository's test suite, so every command and every number below
is the real output of the version you are reading. Work through it in a scratch directory.

```bash
pip install khelsutra-evidence
```

## 1. Start a workspace

```bash
evidence init hall-evidence
```

```json
{
  "files": [
    "hall-evidence/task-profile.json",
    "hall-evidence/scenario-profile.json",
    "hall-evidence/README.md"
  ],
  "status": "created"
}
```

The starter is synthetic. Replace both profiles with what you actually ran.

The **task profile** says what the task is and how it is scored. Fixing the tolerance here is what makes
two builders' numbers mean the same thing.

```bash
cat > hall-evidence/task-profile.json <<'JSON'
{
  "schema_name": "TaskProfileV1",
  "schema_version": "1.0.0",
  "record_id": "task-hall-rally-boundaries",
  "task_id": "hall-rally-boundaries",
  "sport": "badminton",
  "prediction_unit": "rally_boundary",
  "boundary_tolerance_frames": 15,
  "scorer": {"name": "khelsutra-rally-boundary", "version": "1.0.0"},
  "sample_ids": ["hall-2026-03-14"],
  "notes": "One evening session in a three-court hall."
}
JSON
```

The **scenario profile** says what the camera actually saw. Three courts were visible and two games were
running; that is not a footnote, it is the difficulty of the sample.

```bash
cat > hall-evidence/scenario-profile.json <<'JSON'
{
  "schema_name": "ScenarioProfileV1",
  "schema_version": "1.0.0",
  "record_id": "scenario-hall-2026-03-14",
  "sample_id": "hall-2026-03-14",
  "visible_courts": 3,
  "simultaneously_active_games": 2,
  "target_court_id": "court-a",
  "camera": {"motion": "fixed", "angle": "corner", "placement": "tripod at the back wall"},
  "capture": {"width": 1920, "height": 1080, "fps": 30, "cuts": 0, "audio_available": true,
              "lighting": "uneven", "occlusion": "partial"},
  "source_duration_seconds": 1800,
  "adult_rights_cleared": true,
  "notes": "Two games were running while court-a was the target."
}
JSON
```

## 2. Record what a human confirmed, and what the model produced

Truth and prediction use the same contract and differ by `role`. Every rally carries its **provenance**:
a human-confirmed boundary and a model guess are not the same kind of claim, and the framework refuses to
let you blur them — a `model_observation` must name its model and its confidence.

```bash
cat > hall-evidence/truth.json <<'JSON'
{
  "schema_name": "RallyBoundarySetV1",
  "schema_version": "1.0.0",
  "record_id": "truth-hall-2026-03-14",
  "sample_id": "hall-2026-03-14",
  "role": "truth",
  "fps": 30,
  "rallies": [
    {"rally_id": "truth-rally-01", "start_frame": 1200, "end_frame": 1980, "target_court_id": "court-a",
     "provenance": {"authority": "human_confirmed", "confirmed_at": "2026-03-15T09:00:00Z"}},
    {"rally_id": "truth-rally-02", "start_frame": 2400, "end_frame": 3150, "target_court_id": "court-a",
     "provenance": {"authority": "human_confirmed", "confirmed_at": "2026-03-15T09:04:00Z"}},
    {"rally_id": "truth-rally-03", "start_frame": 4200, "end_frame": 4800, "target_court_id": "court-b",
     "provenance": {"authority": "human_confirmed", "confirmed_at": "2026-03-15T09:07:00Z"}}
  ]
}
JSON
```

```bash
cat > hall-evidence/prediction.json <<'JSON'
{
  "schema_name": "RallyBoundarySetV1",
  "schema_version": "1.0.0",
  "record_id": "swiftcourt-hall-2026-03-14",
  "sample_id": "hall-2026-03-14",
  "role": "prediction",
  "fps": 30,
  "rallies": [
    {"rally_id": "swiftcourt-rally-01", "start_frame": 1206, "end_frame": 1972,
     "target_court_id": "court-a",
     "provenance": {"authority": "model_observation", "model_id": "swiftcourt-0.4.1",
                    "confidence": 0.91}},
    {"rally_id": "swiftcourt-rally-02", "start_frame": 2448, "end_frame": 3150,
     "target_court_id": "court-a",
     "provenance": {"authority": "model_observation", "model_id": "swiftcourt-0.4.1",
                    "confidence": 0.72}},
    {"rally_id": "swiftcourt-rally-03", "start_frame": 4200, "end_frame": 4800,
     "target_court_id": "court-a",
     "provenance": {"authority": "model_observation", "model_id": "swiftcourt-0.4.1",
                    "confidence": 0.66}}
  ]
}
JSON
```

```bash
evidence verify hall-evidence
```

```json
{
  "documents": 4,
  "status": "valid"
}
```

## 3. Score it, and read the result you actually got

```bash
evidence score hall-evidence/truth.json hall-evidence/prediction.json --tolerance-frames 15
```

```json
{
  "f1": 0.3333333333333333,
  "matched_count": 1,
  "matches": [
    {
      "end_error_frames": 8,
      "prediction_id": "swiftcourt-rally-01",
      "start_error_frames": 6,
      "truth_id": "truth-rally-01"
    }
  ],
  "precision": 0.3333333333333333,
  "recall": 0.3333333333333333,
  "truth_count": 3,
  "unmatched_prediction_ids": ["swiftcourt-rally-02", "swiftcourt-rally-03"],
  "unmatched_truth_ids": ["truth-rally-02", "truth-rally-03"]
}
```

One of three. The two misses are different failures and the output keeps them apart:

- `swiftcourt-rally-02` starts 48 frames late. That is beyond the 15-frame tolerance **you** declared, so
  it does not count. Widen the tolerance and it would — which is exactly why the tolerance lives in a
  published task profile instead of in your scoring script.
- `swiftcourt-rally-03` has the boundaries exactly right but calls it `court-a` when it happened on
  `court-b`. Matching is court-aware, so a rally found on the wrong court earns nothing. In a hall with
  two games running, this is the failure that a single overall number would have hidden.

The scorer also refuses inputs that contradict themselves — two overlapping rallies on one court cannot
both be real, and it will say so rather than score them.

## 4. Compare against another builder

Another builder publishes a run against the same task contract. Your run carries a cost receipt; theirs
does not.

```bash
cat > hall-evidence/run-swiftcourt.json <<'JSON'
{
  "schema_name": "SystemRunV1",
  "schema_version": "1.0.0",
  "record_id": "run-swiftcourt-0-4-1",
  "run_id": "swiftcourt-0-4-1",
  "run_class": "community",
  "system": {"name": "swiftcourt", "version": "0.4.1",
             "digest": {"algorithm": "sha256",
                        "value": "11111111111111111111111111111111111111111111111111111111111111ab"}},
  "task_contract": {"task_id": "hall-rally-boundaries", "prediction_unit": "rally_boundary",
                    "boundary_tolerance_frames": 15,
                    "scorer_name": "khelsutra-rally-boundary", "scorer_version": "1.0.0"},
  "samples": [{"sample_id": "hall-2026-03-14", "status": "accepted",
               "manual_correction_minutes": 6}],
  "scenario_strata": ["multi-active-fixed"],
  "metrics": [{"name": "tol_f1", "value": 0.3333333333333333, "unit": "ratio",
               "numerator": 1, "denominator": 3, "stratum": "multi-active-fixed"}],
  "timings": [{"phase": "delivery_complete", "elapsed_seconds": 1500}],
  "cost_receipt": {
    "schema_name": "CostReceiptV1", "schema_version": "1.0.0",
    "record_id": "cost-swiftcourt-0-4-1",
    "currency": "USD", "source_seconds": 1800, "accepted_source_seconds": 1800,
    "inference_usd": 0.9, "accelerator_seconds": 1200, "wall_seconds": 1500, "retry_usd": 0,
    "manual_review_minutes": 6, "total_cost_usd": 1.2,
    "inference_usd_per_source_hour": 1.8, "accelerator_seconds_per_source_hour": 2400,
    "wall_seconds_per_source_hour": 3000, "manual_minutes_per_source_hour": 12,
    "total_cost_usd_per_accepted_source_hour": 2.4
  },
  "failures_included": true,
  "notes": "One evening session. Court attribution is the known weak point."
}
JSON
```

Every derived rate keeps its raw numerator and denominator, and the verifier recomputes it. You cannot
publish a cost-per-hour that your own raw numbers do not produce.

```bash
cat > hall-evidence/run-courtwatch.json <<'JSON'
{
  "schema_name": "SystemRunV1",
  "schema_version": "1.0.0",
  "record_id": "run-courtwatch-2-0",
  "run_id": "courtwatch-2-0",
  "run_class": "community",
  "system": {"name": "courtwatch", "version": "2.0",
             "digest": {"algorithm": "sha256",
                        "value": "22222222222222222222222222222222222222222222222222222222222222cd"}},
  "task_contract": {"task_id": "hall-rally-boundaries", "prediction_unit": "rally_boundary",
                    "boundary_tolerance_frames": 15,
                    "scorer_name": "khelsutra-rally-boundary", "scorer_version": "1.0.0"},
  "samples": [{"sample_id": "hall-2026-03-14", "status": "accepted"}],
  "scenario_strata": ["multi-active-fixed"],
  "metrics": [{"name": "tol_f1", "value": 0.6666666666666666, "unit": "ratio",
               "numerator": 2, "denominator": 3, "stratum": "multi-active-fixed"}],
  "timings": [],
  "failures_included": true,
  "notes": "Published by another builder against the same task contract."
}
JSON
```

```bash
evidence compare hall-evidence/run-swiftcourt.json hall-evidence/run-courtwatch.json
```

```json
{
  "cost_comparable": false,
  "quality_comparable": true,
  "reasons": ["task, scorer, samples, and strata match; cost evidence is incomplete"],
  "shared_sample_ids": ["hall-2026-03-14"],
  "verdict": "paired_quality_only"
}
```

They scored better than you on this sample. The verdict tells you precisely how far that comparison
carries: `paired_quality_only` means you may compare quality and may **not** say anything about their
cost, because they did not publish one. Had they used a different scorer version the verdict would be
`incompatible`, and the two numbers would not belong on the same axis at all.

A verdict is a statement about whether two artifacts can be compared. It never certifies a model, a
vendor, or a coaching conclusion.

## 5. Publish without leaking

Your private receipt holds more than you may publish. Rather than asking you to redact by hand, the
framework asks you to classify: one public document, your private material, and the authority that
permits publication. Anything you leave unclassified fails the contract.

```bash
cat > hall-evidence/private-record.json <<'JSON'
{
  "schema_name": "PrivateEvidenceRecordV1",
  "schema_version": "1.0.0",
  "record_id": "private-swiftcourt-hall-2026-03-14",
  "producer": {"repository": "swiftcourt",
               "revision": "0000000000000000000000000000000000000000",
               "receipt_id": "receipt-hall-2026-03-14"},
  "public": {
    "schema_name": "SystemRunV1",
    "schema_version": "1.0.0",
    "record_id": "run-swiftcourt-0-4-1",
    "run_id": "swiftcourt-0-4-1",
    "run_class": "community",
    "system": {"name": "swiftcourt", "version": "0.4.1",
               "digest": {"algorithm": "sha256",
                          "value": "11111111111111111111111111111111111111111111111111111111111111ab"}},
    "task_contract": {"task_id": "hall-rally-boundaries", "prediction_unit": "rally_boundary",
                      "boundary_tolerance_frames": 15,
                      "scorer_name": "khelsutra-rally-boundary", "scorer_version": "1.0.0"},
    "samples": [{"sample_id": "hall-2026-03-14", "status": "accepted",
                 "manual_correction_minutes": 6}],
    "scenario_strata": ["multi-active-fixed"],
    "metrics": [{"name": "tol_f1", "value": 0.3333333333333333, "unit": "ratio",
                 "numerator": 1, "denominator": 3, "stratum": "multi-active-fixed"}],
    "timings": [{"phase": "delivery_complete", "elapsed_seconds": 1500}],
    "cost_receipt": {
      "schema_name": "CostReceiptV1", "schema_version": "1.0.0",
      "record_id": "cost-swiftcourt-0-4-1",
      "currency": "USD", "source_seconds": 1800, "accepted_source_seconds": 1800,
      "inference_usd": 0.9, "accelerator_seconds": 1200, "wall_seconds": 1500, "retry_usd": 0,
      "manual_review_minutes": 6, "total_cost_usd": 1.2,
      "inference_usd_per_source_hour": 1.8, "accelerator_seconds_per_source_hour": 2400,
      "wall_seconds_per_source_hour": 3000, "manual_minutes_per_source_hour": 12,
      "total_cost_usd_per_accepted_source_hour": 2.4
    },
    "failures_included": true,
    "notes": "One evening session. Court attribution is the known weak point. Masters staged at /home/asha/captures/hall-2026-03-14 before inference."
  },
  "private_extensions": {"operator": "asha",
                         "internal_ticket": "SC-4182 court attribution regression"},
  "media_authorizations": [],
  "projection": {"public_record_digest": {"algorithm": "sha256",
                 "value": "0000000000000000000000000000000000000000000000000000000000000000"}}
}
JSON
```

```bash exit=1
evidence project hall-evidence/private-record.json
```

```json
{
  "refusals": [
    {
      "message": "contains local Unix path",
      "path": "public.notes",
      "reason": "unsafe_public_value"
    },
    {
      "message": "must equal the canonical public record digest da197b6578123d5a7ed770cb42320c55d9ea4f3a27cb0a0ab594efdefe7aa3db",
      "path": "projection.public_record_digest.value",
      "reason": "projection_digest_mismatch"
    }
  ],
  "status": "refused"
}
```

Refused, and not quietly fixed. Two things were wrong and both are named in one pass:

- A staging path from your laptop survived into the notes. Publication is not a redaction exercise; the
  tool will not strip it for you and pretend nothing happened.
- The digest you declared does not bind these bytes. The message names the digest that does, so you can
  paste it once the content is final.

Drop the path first. The digest binds the exact bytes, so it changes when the content does — the
`da197b65…` above belongs to the version with the path still in it. Fix the notes, run `project` again,
and paste the digest that refusal names. That second run is why the value below is `45648e00…` and not
the one you just saw.

```bash
cat > hall-evidence/private-record.json <<'JSON'
{
  "schema_name": "PrivateEvidenceRecordV1",
  "schema_version": "1.0.0",
  "record_id": "private-swiftcourt-hall-2026-03-14",
  "producer": {"repository": "swiftcourt",
               "revision": "0000000000000000000000000000000000000000",
               "receipt_id": "receipt-hall-2026-03-14"},
  "public": {
    "schema_name": "SystemRunV1",
    "schema_version": "1.0.0",
    "record_id": "run-swiftcourt-0-4-1",
    "run_id": "swiftcourt-0-4-1",
    "run_class": "community",
    "system": {"name": "swiftcourt", "version": "0.4.1",
               "digest": {"algorithm": "sha256",
                          "value": "11111111111111111111111111111111111111111111111111111111111111ab"}},
    "task_contract": {"task_id": "hall-rally-boundaries", "prediction_unit": "rally_boundary",
                      "boundary_tolerance_frames": 15,
                      "scorer_name": "khelsutra-rally-boundary", "scorer_version": "1.0.0"},
    "samples": [{"sample_id": "hall-2026-03-14", "status": "accepted",
                 "manual_correction_minutes": 6}],
    "scenario_strata": ["multi-active-fixed"],
    "metrics": [{"name": "tol_f1", "value": 0.3333333333333333, "unit": "ratio",
                 "numerator": 1, "denominator": 3, "stratum": "multi-active-fixed"}],
    "timings": [{"phase": "delivery_complete", "elapsed_seconds": 1500}],
    "cost_receipt": {
      "schema_name": "CostReceiptV1", "schema_version": "1.0.0",
      "record_id": "cost-swiftcourt-0-4-1",
      "currency": "USD", "source_seconds": 1800, "accepted_source_seconds": 1800,
      "inference_usd": 0.9, "accelerator_seconds": 1200, "wall_seconds": 1500, "retry_usd": 0,
      "manual_review_minutes": 6, "total_cost_usd": 1.2,
      "inference_usd_per_source_hour": 1.8, "accelerator_seconds_per_source_hour": 2400,
      "wall_seconds_per_source_hour": 3000, "manual_minutes_per_source_hour": 12,
      "total_cost_usd_per_accepted_source_hour": 2.4
    },
    "failures_included": true,
    "notes": "One evening session. Court attribution is the known weak point."
  },
  "private_extensions": {"operator": "asha",
                         "internal_ticket": "SC-4182 court attribution regression"},
  "media_authorizations": [],
  "projection": {"public_record_digest": {"algorithm": "sha256",
                 "value": "45648e00af7b579eab91cbe3771dcc287b89dbf87465100988f03004e3b2d019"}}
}
JSON
```

```bash
mkdir -p publish
evidence project hall-evidence/private-record.json --output publish/run-swiftcourt.json
sha256sum publish/run-swiftcourt.json
```

```
45648e00af7b579eab91cbe3771dcc287b89dbf87465100988f03004e3b2d019  publish/run-swiftcourt.json
```

The published file's SHA-256 is the digest your private record declared. Anyone who has the public file
can check that it is exactly what you bound, and neither of you has to trust the other's tooling to do
it. `evidence project ... | sha256sum` gives the same answer without writing a file.

`operator` and `internal_ticket` never appear in the output. They are not stripped — they were never
publishable, and the projector would have refused if either value had reappeared in the public payload.

## 6. Package it

```bash
evidence package publish swiftcourt-evidence.tar.gz
```

```json
{
  "path": "swiftcourt-evidence.tar.gz",
  "sha256": "ec2eaff5c9ed9ab71f8a5683f5f5d400f9395e897f59ec03abf47bb702932ed4",
  "status": "packaged"
}
```

The archive is byte-deterministic: same inputs, same digest, on any machine. Packaging validates every
document again and scans for secrets, private endpoints, and local paths, so the last gate before you
hand someone a file is the same gate as the first.

## What you may now say, and what you may not

You may say: on one 30-minute session in a three-court hall, with a 15-frame tolerance, your detector
matched one of three human-confirmed rallies, at USD 2.40 per accepted source hour, and another builder
matched two of three on the same contract with no cost evidence published.

You may not say your detector is 33% accurate, that the other builder's is better, or that any of this
is a blind or independent benchmark. One sample is one sample; you chose it; nothing here was sealed.

And no number in this walkthrough is a coaching claim. The framework exists to keep a model score from
quietly becoming advice to a player. The coach decides what it means.

## Where to go next

- [Comparability verdicts](COMPARABILITY.md) — what each verdict permits.
- [Private superset and public projection](PROJECTION.md) — the full refusal list.
- [Publication safety](PUBLICATION.md) — what the scanner cannot check, and still needs a human.
- [Schema guide](SCHEMAS.md) — every contract in v1.
