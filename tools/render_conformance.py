"""Render the portable conformance suite from the reference implementation.

Every expectation in `conformance/v1/manifest.json` is produced by running the reference
implementation, never written by hand, so the corpus cannot drift from the behaviour it claims to
pin. Re-run this after any deliberate behaviour change:

    python tools/render_conformance.py

`tests/test_conformance.py` fails if the checked-in file differs from what this renders, and replays
every case through the public API the way a foreign implementation would.
"""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from khelsutra_evidence.comparison import compare_runs
from khelsutra_evidence.packaging import archive_members, package_directory
from khelsutra_evidence.projection import projection_refusals, public_record_digest
from khelsutra_evidence.schemas import schemas_by_name, validator_for
from khelsutra_evidence.scoring import score_rallies
from khelsutra_evidence.validation import (
    canonical_plan_digest,
    canonical_recipe_digest,
    canonical_suite_digest,
    safety_issues,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
MANIFEST = ROOT / "conformance" / "v1" / "manifest.json"

JsonObject = dict[str, Any]


def example(relative: str) -> JsonObject:
    loaded: JsonObject = json.loads((EXAMPLES / relative).read_text(encoding="utf-8"))
    return loaded


def fixture(relative: str) -> JsonObject:
    loaded: JsonObject = json.loads((FIXTURES / relative).read_text(encoding="utf-8"))
    return loaded


def _failure_stage(document: JsonObject) -> str:
    """Say which layer rejected a document, because only two of the three are portable.

    `structural` and `semantic` messages are authored in this repository and are normative.
    `schema` messages come from whichever JSON Schema library an implementation uses, so only the
    issue paths are normative there.
    """
    name = document.get("schema_name")
    if not isinstance(name, str) or name not in schemas_by_name():
        return "structural"
    return "schema" if list(validator_for(name).iter_errors(document)) else "semantic"


def validate_case(case_id: str, title: str, document: JsonObject) -> JsonObject:
    issues = validate_document(document)
    expect: JsonObject = {
        "valid": not issues,
        "stage": _failure_stage(document) if issues else None,
        "issue_paths": sorted({issue.path for issue in issues}),
        "messages": [issue.render() for issue in issues],
    }
    return {
        "case_id": case_id,
        "operation": "validate_document",
        "title": title,
        "input": {"document": document},
        "expect": expect,
    }


def score_case(
    case_id: str, title: str, truth: JsonObject, prediction: JsonObject, tolerance: int
) -> JsonObject:
    try:
        expect: JsonObject = {"result": score_rallies(truth, prediction, tolerance)}
    except ValueError as exc:
        expect = {"error": str(exc)}
    return {
        "case_id": case_id,
        "operation": "score_rallies",
        "title": title,
        "input": {"truth": truth, "prediction": prediction, "tolerance_frames": tolerance},
        "expect": expect,
    }


def compare_case(case_id: str, title: str, left: JsonObject, right: JsonObject) -> JsonObject:
    try:
        expect: JsonObject = {"result": compare_runs(left, right)}
    except ValueError as exc:
        expect = {"error": str(exc)}
    return {
        "case_id": case_id,
        "operation": "compare_runs",
        "title": title,
        "input": {"left": left, "right": right},
        "expect": expect,
    }


def digest_case(case_id: str, title: str, operation: str, document: JsonObject) -> JsonObject:
    compute = canonical_plan_digest if operation == "plan_digest" else canonical_recipe_digest
    return {
        "case_id": case_id,
        "operation": operation,
        "title": title,
        "input": {"document": document},
        "expect": {"digest": compute(document)},
    }


def safety_case(case_id: str, title: str, value: Any) -> JsonObject:
    return {
        "case_id": case_id,
        "operation": "public_safety",
        "title": title,
        "input": {"value": value},
        "expect": {"issues": [issue.render() for issue in safety_issues(value)]},
    }


def projection_case(case_id: str, title: str, record: JsonObject) -> JsonObject:
    refusals = projection_refusals(record)
    expect: JsonObject = {
        "refusals": [
            {"reason": item.reason, "path": item.path, "message": item.message} for item in refusals
        ]
    }
    if not refusals:
        expect["public_record_digest"] = public_record_digest(record["public"])
    return {
        "case_id": case_id,
        "operation": "project_record",
        "title": title,
        "input": {"record": record},
        "expect": expect,
    }


def package_case(case_id: str, title: str, files: list[JsonObject]) -> JsonObject:
    with tempfile.TemporaryDirectory() as raw:
        source = Path(raw) / "source"
        source.mkdir()
        for entry in files:
            (source / str(entry["name"])).write_text(str(entry["text"]), encoding="utf-8")
        destination = Path(raw) / "archive.tar.gz"
        try:
            sha256 = package_directory(source, destination)
            expect: JsonObject = {"members": archive_members(destination), "sha256": sha256}
        except ValueError as exc:
            expect = {"error": str(exc).replace(f"{source}/", "")}
    return {
        "case_id": case_id,
        "operation": "package_archive",
        "title": title,
        "input": {"files": files},
        "expect": expect,
    }


def _cross_court_pair() -> tuple[JsonObject, JsonObject]:
    truth = example("rallies/truth.json")
    prediction = copy.deepcopy(truth)
    prediction["schema_name"] = "RallyBoundarySetV1"
    prediction["role"] = "prediction"
    prediction["record_id"] = "rally-set-cross-court-prediction"
    for index, rally in enumerate(prediction["rallies"]):
        rally["rally_id"] = f"cross-court-prediction-{index}"
        rally["target_court_id"] = f"{rally['target_court_id']}-other"
        rally["provenance"] = {
            "authority": "model_observation",
            "model_id": "synthetic-model",
            "confidence": 0.9,
        }
    return truth, prediction


def build_cases() -> list[JsonObject]:
    cases: list[JsonObject] = []

    # --- document validation, valid and invalid, with exact issue paths and messages -------------
    cases.append(
        validate_case(
            "validate-scenario-profile-accepted",
            "A synthetic scenario profile validates with no issues.",
            example("scenario-profile.json"),
        )
    )
    scenario = example("scenario-profile.json")
    scenario["simultaneously_active_games"] = scenario["visible_courts"] + 1
    cases.append(
        validate_case(
            "validate-scenario-active-exceeds-visible",
            "Simultaneously active games cannot exceed the visible courts.",
            scenario,
        )
    )
    cost = example("cost-receipt.json")
    cost["inference_usd_per_source_hour"] = 99.0
    cases.append(
        validate_case(
            "validate-cost-rate-not-derived-from-raw",
            "A derived cost rate must equal its raw numerator over its denominator.",
            cost,
        )
    )
    commercialization = example("commercialization-readiness.json")
    commercialization["components"][-1]["category"] = commercialization["components"][0]["category"]
    cases.append(
        validate_case(
            "validate-commercialization-duplicate-and-missing-category",
            "All nine commercialization categories must be present exactly once.",
            commercialization,
        )
    )
    adaptation = example("owner-adaptation.json")
    adaptation["heldout_sample_ids"] = list(adaptation["training_sample_ids"])
    cases.append(
        validate_case(
            "validate-adaptation-heldout-overlaps-training",
            "Held-out samples must be disjoint from training samples.",
            adaptation,
        )
    )
    release = example("evidence-release.json")
    release["release_class"] = "blind"
    cases.append(
        validate_case(
            "validate-release-blind-cannot-be-exposed",
            "A blind release cannot be marked exposed before freeze.",
            release,
        )
    )
    prediction = example("rallies/prediction.json")
    prediction["rallies"][0]["provenance"].pop("model_id")
    prediction["rallies"][0]["provenance"].pop("confidence")
    cases.append(
        validate_case(
            "validate-model-observation-missing-identity",
            "A model observation must carry its model identity and confidence.",
            prediction,
        )
    )
    task = example("task-profile.json")
    task["internal_owner"] = "unclassified"
    cases.append(
        validate_case(
            "validate-undeclared-field-is-rejected",
            "Public contracts are closed; an undeclared field fails validation.",
            task,
        )
    )
    cases.append(
        validate_case(
            "validate-unknown-schema-name-fails-closed",
            "An unrecognised schema name fails closed instead of being skipped.",
            {"schema_name": "NotAContractV1", "schema_version": "1.0.0"},
        )
    )
    rally_set = example("rallies/truth.json")
    overlapping = copy.deepcopy(rally_set["rallies"][0])
    overlapping["rally_id"] = "overlapping-rally"
    overlapping["start_frame"] = int(rally_set["rallies"][0]["start_frame"]) + 1
    rally_set["rallies"].append(overlapping)
    cases.append(
        validate_case(
            "validate-rally-overlap-on-one-court",
            "Rallies on the same court must not overlap.",
            rally_set,
        )
    )
    cases.append(
        validate_case(
            "validate-private-record-accepted",
            "A synthetic private evidence record validates with no issues.",
            example("private-evidence-record.json"),
        )
    )

    # --- court-aware reference scoring ------------------------------------------------------------
    cases.append(
        score_case(
            "score-synthetic-sample-tolerance-15",
            "Reference scoring of the synthetic sample at a 15-frame tolerance.",
            example("rallies/truth.json"),
            example("rallies/prediction.json"),
            15,
        )
    )
    cross_truth, cross_prediction = _cross_court_pair()
    cases.append(
        score_case(
            "score-does-not-match-across-courts",
            "Identical boundaries on a different court are not a match.",
            cross_truth,
            cross_prediction,
            15,
        )
    )
    mismatched = example("rallies/prediction.json")
    mismatched["sample_id"] = "synthetic-match-999"
    cases.append(
        score_case(
            "score-rejects-mismatched-sample-id",
            "Truth and prediction must describe the same sample.",
            example("rallies/truth.json"),
            mismatched,
            15,
        )
    )

    # --- comparability verdicts and their reasons -------------------------------------------------
    left = example("runs/system-a.json")
    twin = example("runs/system-a.json")
    twin["run_id"] = "synthetic-run-a-twin"
    twin["record_id"] = "system-run-synthetic-a-twin"
    cases.append(
        compare_case(
            "compare-paired-runs",
            "Matching task, samples, strata, and cost evidence pair fully.",
            left,
            twin,
        )
    )
    cases.append(
        compare_case(
            "compare-paired-quality-only",
            "Matching quality evidence without complete cost evidence pairs on quality only.",
            example("runs/system-a.json"),
            example("runs/system-b.json"),
        )
    )
    partial = example("runs/system-a.json")
    partial["run_id"] = "synthetic-run-a-extra"
    partial["record_id"] = "system-run-synthetic-a-extra"
    partial["samples"].append({"sample_id": "synthetic-match-002", "status": "accepted"})
    cases.append(
        compare_case(
            "compare-partially-comparable",
            "A strict subset of shared samples is only partially comparable.",
            example("runs/system-a.json"),
            partial,
        )
    )
    disjoint = example("runs/system-a.json")
    disjoint["run_id"] = "synthetic-run-a-disjoint"
    disjoint["record_id"] = "system-run-synthetic-a-disjoint"
    disjoint["samples"] = [{"sample_id": "synthetic-match-777", "status": "accepted"}]
    cases.append(
        compare_case(
            "compare-descriptive-only",
            "A matching contract with no shared samples is descriptive only.",
            example("runs/system-a.json"),
            disjoint,
        )
    )
    incompatible = example("runs/system-a.json")
    incompatible["run_id"] = "synthetic-run-a-other-scorer"
    incompatible["record_id"] = "system-run-synthetic-a-other-scorer"
    incompatible["task_contract"]["scorer_version"] = "2.0.0"
    cases.append(
        compare_case(
            "compare-incompatible-task-contract",
            "A different scorer version makes two runs incompatible.",
            example("runs/system-a.json"),
            incompatible,
        )
    )

    # --- canonical content-addressed identities ---------------------------------------------------
    cases.append(
        digest_case(
            "digest-coach-instruction-plan",
            "The canonical plan digest over the plan's normative fields.",
            "plan_digest",
            example("coach-instruction-plan.json"),
        )
    )
    cases.append(
        digest_case(
            "digest-evidence-recipe",
            "The canonical recipe digest over plan, items, and rendition.",
            "recipe_digest",
            example("evidence-recipe.json"),
        )
    )

    # --- public-safety scanning -------------------------------------------------------------------
    # Provider-token shapes are exercised in the reference implementation's own tests and are
    # deliberately absent here; see docs/CONFORMANCE.md.
    cases.append(
        safety_case(
            "safety-accepts-synthetic-public-value",
            "An ordinary synthetic public value raises no issue.",
            {"notes": "Synthetic contract fixture; not product evidence."},
        )
    )
    cases.append(
        safety_case(
            "safety-rejects-private-ipv4-endpoint",
            "A private IPv4 endpoint is not publishable.",
            "Rendered by the worker at http://192.168.1.2:9000.",
        )
    )
    cases.append(
        safety_case(
            "safety-rejects-local-unix-path",
            "A local filesystem path is not publishable.",
            "Master unavailable at /home/operator/masters/match-5.mp4.",
        )
    )
    cases.append(
        safety_case(
            "safety-rejects-loopback-and-tailnet-endpoints",
            "Loopback and tailnet endpoints are not publishable.",
            ["http://localhost:8000", "internal.example.ts.net"],
        )
    )
    cases.append(
        safety_case(
            "safety-rejects-signed-url-credential",
            "A signed-URL credential parameter is not publishable.",
            "https://example.invalid/object?X-Amz-Signature=not-public",
        )
    )
    cases.append(
        safety_case(
            "safety-rejects-private-only-field-name",
            "A private-only field name is not publishable even when its value looks harmless.",
            {"checkpoint_path": "redacted"},
        )
    )

    # --- private superset to public projection ----------------------------------------------------
    cases.append(
        projection_case(
            "project-publishes-authorized-record",
            "An authorised private record projects to its declared public digest.",
            example("private-evidence-record.json"),
        )
    )
    cases.append(
        projection_case(
            "project-refuses-unlisted-media",
            "Published media without an authorization is refused.",
            fixture("projection/unlisted-media.json"),
        )
    )
    cases.append(
        projection_case(
            "project-refuses-unbound-digest",
            "A declared public digest that does not bind the projected bytes is refused.",
            fixture("projection/projection-digest-mismatch.json"),
        )
    )
    cases.append(
        projection_case(
            "project-refuses-echoed-private-value",
            "A private extension value repeated in the projection is refused.",
            fixture("projection/private-value-echo.json"),
        )
    )

    # --- deterministic packaging ------------------------------------------------------------------
    cases.append(
        package_case(
            "package-deterministic-archive",
            "A public package has stable members and a stable archive digest.",
            [
                {"name": "README.md", "text": "# Safe synthetic package\n"},
                {
                    "name": "task.json",
                    "text": json.dumps(example("task-profile.json"), sort_keys=True),
                },
            ],
        )
    )
    unsafe_task = example("task-profile.json")
    unsafe_task["notes"] = "Rendered by the worker at http://192.168.1.2:9000."
    cases.append(
        package_case(
            "package-refuses-unsafe-value",
            "Packaging refuses a document carrying a private endpoint.",
            [{"name": "task.json", "text": json.dumps(unsafe_task, sort_keys=True)}],
        )
    )

    return sorted(cases, key=lambda case: str(case["case_id"]))


def build_suite() -> JsonObject:
    suite: JsonObject = {
        "schema_name": "ConformanceSuiteV1",
        "schema_version": "1.0.0",
        "record_id": "khelsutra-evidence-conformance-v1",
        "suite_id": "khelsutra-evidence-conformance-v1",
        "contract_version": "v1",
        "suite_digest": {"algorithm": "sha256", "value": "0" * 64},
        "cases": build_cases(),
    }
    suite["suite_digest"]["value"] = canonical_suite_digest(suite)
    return suite


def render() -> str:
    return json.dumps(build_suite(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(render(), encoding="utf-8")
    suite = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print(f"{MANIFEST.relative_to(ROOT)}: {len(suite['cases'])} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
