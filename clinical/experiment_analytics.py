"""Aggregate sanitized synthetic experiment history for research visualization."""
from collections import defaultdict
from .experiment_history import ExperimentRecord

def analytics(records: tuple[ExperimentRecord, ...]) -> dict:
    ordered = sorted(records, key=lambda r: (r.recorded_at, r.run_id))
    trends = [{"run_id": r.run_id, "recorded_at": r.recorded_at,
               "model": r.model, "total": r.total, "model_returned": r.model_returned,
               "disagreement_count": r.disagreement_count,
               "disagreement_rate": r.disagreement_rate} for r in ordered]
    by_model: dict[str, list[ExperimentRecord]] = defaultdict(list)
    for record in ordered:
        by_model[record.model].append(record)
    models = []
    for name, rows in sorted(by_model.items()):
        evaluated = sum(r.model_returned for r in rows)
        disagreements = sum(r.disagreement_count for r in rows)
        models.append({"model": name, "runs": len(rows), "judgments": evaluated,
                       "disagreements": disagreements,
                       "weighted_disagreement_rate": round(disagreements / evaluated, 4) if evaluated else None})
    return {"runs": len(ordered), "trends": trends, "models": models,
            "disclaimer": "Synthetic screening disagreement only; not clinical accuracy."}
