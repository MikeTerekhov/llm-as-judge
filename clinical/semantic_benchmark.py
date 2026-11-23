"""Compare NLI screening and lexical screening on the fictional adversarial set.

Hand-authored semantic labels are NOT independent clinical ground truth.
"""
from .adversarial_fixtures import AdversarialExample, SemanticLabel
from .claim_judge import JudgeStatus
from .semantic_judge import NLIScorer, judge_claim_semantic

LABEL_VALUES = tuple(label.value for label in SemanticLabel)

def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None

def benchmark_semantic(examples: tuple[AdversarialExample, ...], scorer: NLIScorer | None,
                       *, scorer_name: str = "unconfigured", **thresholds) -> dict:
    if not examples:
        raise ValueError("Dataset must not be empty")
    if len({e.example_id for e in examples}) != len(examples):
        raise ValueError("Duplicate example IDs")
    rows = []
    confusion = {expected: {**{p: 0 for p in LABEL_VALUES}, "abstain": 0}
                 for expected in LABEL_VALUES}
    by_category: dict[str, dict[str, int]] = {}
    returned = matched = false_support = lexical_false_assurance = 0
    for example in examples:
        judgment = judge_claim_semantic(example.claim, example.evidence, scorer, **thresholds)
        verdict = judgment.verdict.value if judgment.verdict else None
        expected = example.expected.value
        confusion[expected][verdict or "abstain"] += 1
        agreement = verdict == expected if verdict is not None else None
        # The safety-relevant error: calling a claim supported when it is not.
        is_false_support = verdict == SemanticLabel.SUPPORTED.value and expected != verdict
        lexical_assurance = (judgment.lexical_status == JudgeStatus.REVIEW_REQUIRED
                             and expected != SemanticLabel.SUPPORTED.value)
        returned += verdict is not None
        matched += agreement is True
        false_support += is_false_support
        lexical_false_assurance += lexical_assurance
        counts = by_category.setdefault(example.category,
                                        {"examples": 0, "nli_returned": 0, "matches": 0})
        counts["examples"] += 1
        counts["nli_returned"] += verdict is not None
        counts["matches"] += agreement is True
        rows.append({
            "id": example.example_id, "category": example.category,
            "expected_semantic_label": expected,
            "lexical_status": judgment.lexical_status.value,
            "nli_verdict": verdict, "disposition": judgment.disposition,
            "matches_hand_authored_label": agreement,
            "false_support": is_false_support,
            "max_entailment": judgment.best_support.scores.entailment if judgment.best_support else None,
            "max_contradiction": (judgment.strongest_conflict.scores.contradiction
                                  if judgment.strongest_conflict else None),
            "reasons": list(judgment.reasons),
        })
    categories = {name: {**counts, "label_agreement_rate": _rate(counts["matches"], counts["nli_returned"])}
                  for name, counts in sorted(by_category.items())}
    return {"total": len(rows), "scorer": scorer_name,
            "thresholds": {"support": thresholds.get("support_threshold", 0.9),
                           "contradiction": thresholds.get("contradiction_threshold", 0.9)},
            "nli_returned": returned, "nli_abstained": len(rows) - returned,
            "label_agreement_rate": _rate(matched, returned),
            "false_support_count": false_support,
            "lexical_false_assurance_count": lexical_false_assurance,
            "confusion_matrix": confusion, "categories": categories, "rows": rows,
            "disclaimer": "Fictional, hand-authored semantic labels; a tiny set that "
                          "cannot establish accuracy or clinical correctness."}
