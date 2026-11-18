"""Compare two synthetic research reports without treating checksums as accuracy."""
from collections import Counter
from .reproducible_report import verify_report

def compare_reports(baseline: dict, current: dict, *, allow_fixture_changes: bool = False) -> dict:
    if not verify_report(baseline) or not verify_report(current):
        raise ValueError("Invalid or tampered report")
    if baseline["schema_version"] != current["schema_version"]:
        raise ValueError("Incompatible report schema")
    old_rows = {row["id"]: row for row in baseline["lexical_benchmark"]["examples"]}
    new_rows = {row["id"]: row for row in current["lexical_benchmark"]["examples"]}
    changed = []
    for example_id in sorted(old_rows.keys() | new_rows.keys()):
        before, after = old_rows.get(example_id), new_rows.get(example_id)
        if before is None or after is None:
            changed.append({"example_id": example_id, "change": "fixture_added_or_removed"})
        elif (before["lexical_status"] != after["lexical_status"] or
              before["potential_false_assurance"] != after["potential_false_assurance"] or
              before["expected_semantic_label"] != after["expected_semantic_label"]):
            changed.append({"example_id": example_id, "change": "evaluation_changed",
                            "before": {"lexical_status": before["lexical_status"],
                                       "potential_false_assurance": before["potential_false_assurance"],
                                       "expected_semantic_label": before["expected_semantic_label"]},
                            "after": {"lexical_status": after["lexical_status"],
                                      "potential_false_assurance": after["potential_false_assurance"],
                                      "expected_semantic_label": after["expected_semantic_label"]}})
    fixture_changed = baseline["dataset_sha256"] != current["dataset_sha256"]
    review_changed = baseline["review_label_counts_sha256"] != current["review_label_counts_sha256"]
    quality_changed = baseline["quality_gates"] != current["quality_gates"]
    blockers = []
    if fixture_changed and not allow_fixture_changes:
        blockers.append("fixture_fingerprint_changed")
    if changed:
        blockers.append("evaluator_or_label_outcomes_changed")
    # Human review data is not evaluated in synthetic CI; changes are reported,
    # not automatically classified as an evaluator regression.
    return {"status": "blocked" if blockers else "pass",
            "blockers": blockers, "fixture_changed": fixture_changed,
            "review_counts_changed": review_changed, "quality_gates_changed": quality_changed,
            "changed_examples": changed, "baseline_sha256": baseline["report_sha256"],
            "current_sha256": current["report_sha256"],
            "disclaimer": "Regression consistency is not clinical or semantic correctness."}
