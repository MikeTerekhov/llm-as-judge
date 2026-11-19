"""Offline, paired comparison of synthetic benchmark run reports.

Never infer clinical accuracy or rank models without returned verdict coverage.
"""
from collections import defaultdict
from clinical.semantic_metrics import LABELS

def _validate_run(data: dict) -> dict:
    if data.get("mode") != "executed" or not isinstance(data.get("model"), str) or not data["model"].strip():
        raise ValueError("Only identified executed benchmark runs can be compared")
    report = data.get("report")
    if not isinstance(report, dict) or not isinstance(report.get("rows"), list):
        raise ValueError("Invalid benchmark report")
    rows = {}
    for row in report["rows"]:
        identifier = row.get("example_id")
        expected = row.get("expected")
        verdict = row.get("model_verdict")
        if not isinstance(identifier, str) or not identifier or identifier in rows:
            raise ValueError("Missing or duplicate fixture ID")
        if expected not in LABELS or verdict not in (*LABELS, None):
            raise ValueError("Invalid authored label or model verdict")
        rows[identifier] = (expected, verdict)
    if len(rows) != 12 or report.get("total") != 12:
        raise ValueError("Expected the complete twelve-fixture benchmark")
    return rows

def compare_runs(runs: list[dict]) -> dict:
    if len(runs) < 2:
        raise ValueError("At least two runs are required")
    normalized = [_validate_run(run) for run in runs]
    reference = {key: value[0] for key, value in normalized[0].items()}
    for rows in normalized[1:]:
        if {key: value[0] for key, value in rows.items()} != reference:
            raise ValueError("Fixture IDs or authored labels differ between runs")
    summaries = []
    for run, rows in zip(runs, normalized):
        returned = sum(verdict is not None for _, verdict in rows.values())
        correct = sum(expected == verdict for expected, verdict in rows.values() if verdict is not None)
        summaries.append({"model": run["model"], "returned": returned, "abstained": len(rows)-returned,
                          "coverage": round(returned / len(rows), 4),
                          "conditional_agreement": round(correct / returned, 4) if returned else None})
    pairs = []
    for i in range(len(runs)):
        for j in range(i+1, len(runs)):
            left, right = normalized[i], normalized[j]
            common = [key for key in sorted(reference)
                      if left[key][1] is not None and right[key][1] is not None]
            left_correct = sum(left[key][1] == reference[key] for key in common)
            right_correct = sum(right[key][1] == reference[key] for key in common)
            disagreements = sum(left[key][1] != right[key][1] for key in common)
            pairs.append({"left_index": i, "right_index": j, "shared_verdicts": len(common),
                          "disagreements": disagreements,
                          "disagreement_rate": round(disagreements/len(common), 4) if common else None,
                          "left_agreement_on_shared": round(left_correct/len(common), 4) if common else None,
                          "right_agreement_on_shared": round(right_correct/len(common), 4) if common else None})
    return {"fixture_count": len(reference), "runs": summaries, "pairs": pairs,
            "disclaimer": "Paired agreement with hand-authored fictional labels only. No independent clinical accuracy or statistical significance established."}
