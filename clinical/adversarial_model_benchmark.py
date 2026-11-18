"""Opt-in adversarial model benchmark on fixed fictional claim/evidence pairs.

Hand-authored semantic labels are NOT independent clinical ground truth.
"""
from dataclasses import dataclass
from typing import Callable

from .adversarial_fixtures import AdversarialExample, SemanticLabel
from .claim_judge import JudgeStatus
from .llm_judge import evaluate_with_model

@dataclass(frozen=True)
class AdversarialModelRow:
    example_id: str
    category: str
    expected: str
    lexical_status: str
    model_verdict: str | None
    disposition: str
    matches_hand_authored_label: bool | None
    lexical_model_disagreement: bool | None

def benchmark_adversarial(examples: tuple[AdversarialExample, ...],
                          model_call: Callable[[str], str] | None = None) -> dict:
    if not examples:
        raise ValueError("Dataset must not be empty")
    if len({e.example_id for e in examples}) != len(examples):
        raise ValueError("Duplicate example IDs")
    rows = []
    by_category: dict[str, dict[str, int]] = {}
    returned = matched = disagreement = 0
    for example in examples:
        result = evaluate_with_model(example.claim, example.evidence, model_call)
        verdict = result.model.verdict.value if result.model else None
        agreement = verdict == example.expected.value if verdict is not None else None
        lexical_disagreement = None
        if verdict is not None:
            returned += 1
            matched += int(agreement)
            # REVIEW_REQUIRED is lexical overlap only, not semantic support.
            lexical_disagreement = ((result.lexical_status == JudgeStatus.REVIEW_REQUIRED) !=
                                    (verdict == SemanticLabel.SUPPORTED.value))
            disagreement += int(lexical_disagreement)
        counts = by_category.setdefault(example.category,
            {"examples": 0, "model_returned": 0, "matches": 0, "disagreements": 0})
        counts["examples"] += 1
        counts["model_returned"] += int(verdict is not None)
        counts["matches"] += int(agreement is True)
        counts["disagreements"] += int(lexical_disagreement is True)
        rows.append(AdversarialModelRow(example.example_id, example.category,
                    example.expected.value, result.lexical_status.value, verdict,
                    result.disposition, agreement, lexical_disagreement))
    categories = {
        category: {**counts,
                   "label_agreement_rate": round(counts["matches"] / counts["model_returned"], 4)
                   if counts["model_returned"] else None,
                   "lexical_disagreement_rate": round(counts["disagreements"] / counts["model_returned"], 4)
                   if counts["model_returned"] else None}
        for category, counts in sorted(by_category.items())
    }
    return {"total": len(rows), "model_returned": returned, "model_abstained": len(rows) - returned,
            "label_agreement_rate": round(matched / returned, 4) if returned else None,
            "lexical_disagreement_rate": round(disagreement / returned, 4) if returned else None,
            "categories": categories,
            "rows": [vars(row) for row in rows],
            "disclaimer": "Fictional, hand-authored semantic labels; not clinical correctness."}
