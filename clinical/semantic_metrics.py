"""Descriptive classification metrics for fictional authored labels.

Metrics are conditional on returned model verdicts and are not clinical accuracy.
"""
from collections import Counter

LABELS = ("supported", "contradicted", "insufficient_evidence")

def classification_metrics(rows: list[dict]) -> dict:
    """Evaluate only returned, recognized verdicts; never count abstentions as errors."""
    confusion = {label: {pred: 0 for pred in LABELS} for label in LABELS}
    total = len(rows)
    evaluated = 0
    for row in rows:
        expected = row["expected"]
        predicted = row["model_verdict"]
        if expected not in LABELS:
            raise ValueError("Unknown authored label")
        if predicted is None:
            continue
        if predicted not in LABELS:
            raise ValueError("Unknown model verdict")
        confusion[expected][predicted] += 1
        evaluated += 1
    per_label = {}
    for label in LABELS:
        tp = confusion[label][label]
        support = sum(confusion[label].values())
        predicted = sum(confusion[actual][label] for actual in LABELS)
        precision = tp / predicted if predicted else None
        recall = tp / support if support else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and recall is not None and precision + recall else None)
        per_label[label] = {"support": support, "predicted": predicted,
                            "precision": round(precision, 4) if precision is not None else None,
                            "recall": round(recall, 4) if recall is not None else None,
                            "f1": round(f1, 4) if f1 is not None else None}
    correct = sum(confusion[label][label] for label in LABELS)
    available_f1 = [metrics["f1"] for metrics in per_label.values() if metrics["f1"] is not None]
    return {"total": total, "evaluated": evaluated, "abstained": total - evaluated,
            "coverage": round(evaluated / total, 4) if total else None,
            "accuracy": round(correct / evaluated, 4) if evaluated else None,
            "macro_f1": round(sum(available_f1) / len(available_f1), 4) if available_f1 else None,
            "confusion": confusion, "per_label": per_label,
            "disclaimer": "Agreement with fictional authored labels only; not independently validated medical accuracy."}
