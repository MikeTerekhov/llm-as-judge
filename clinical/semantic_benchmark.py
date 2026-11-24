"""Compare NLI screening and lexical screening on the fictional adversarial set.

Hand-authored or rule-generated semantic labels are NOT independent clinical ground truth.
"""
from math import sqrt

from .adversarial_fixtures import AdversarialExample, SemanticLabel
from .claim_judge import JudgeStatus
from .semantic_judge import NLIScorer, judge_claim_semantic

LABEL_VALUES = tuple(label.value for label in SemanticLabel)

def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None

def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float] | None:
    """95% Wilson score interval; better than the normal approximation for small n."""
    if not total:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]

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
    by_template: dict[str, dict] = {}
    by_split: dict[str, dict[str, int]] = {}
    returned = matched = false_support = lexical_false_assurance = unsupported = 0
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
        # Lexical screening flagging a claim the labels say is supported.
        lexical_alarm = (judgment.lexical_status != JudgeStatus.REVIEW_REQUIRED
                         and expected == SemanticLabel.SUPPORTED.value)
        returned += verdict is not None
        matched += agreement is True
        false_support += is_false_support
        lexical_false_assurance += lexical_assurance
        unsupported += expected != SemanticLabel.SUPPORTED.value
        groups = [by_category.setdefault(example.category, {}),
                  by_split.setdefault(example.split, {})]
        if example.template:
            template = by_template.setdefault(example.template, {
                "category": example.category, "expected_semantic_label": expected,
                "verdicts": {**{p: 0 for p in LABEL_VALUES}, "abstain": 0}})
            template["verdicts"][verdict or "abstain"] += 1
            groups.append(template)
        for counts in groups:
            for key, value in (("examples", 1), ("nli_returned", verdict is not None),
                               ("matches", agreement is True), ("false_support", is_false_support),
                               ("lexical_false_assurance", lexical_assurance),
                               ("lexical_false_alarm", lexical_alarm)):
                counts[key] = counts.get(key, 0) + int(value)
        rows.append({
            "id": example.example_id, "category": example.category,
            "template": example.template or None, "split": example.split,
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
    def summarise(groups):
        return {name: {**counts,
                       "label_agreement_rate": _rate(counts["matches"], counts["nli_returned"]),
                       "label_agreement_95ci": wilson_interval(counts["matches"], counts["nli_returned"])}
                for name, counts in sorted(groups.items())}
    return {"total": len(rows), "scorer": scorer_name,
            "thresholds": {"support": thresholds.get("support_threshold", 0.9),
                           "contradiction": thresholds.get("contradiction_threshold", 0.9)},
            "nli_returned": returned, "nli_abstained": len(rows) - returned,
            "label_agreement_rate": _rate(matched, returned),
            "label_agreement_95ci": wilson_interval(matched, returned),
            "false_support_count": false_support,
            "false_support_rate": _rate(false_support, unsupported),
            "false_support_95ci": wilson_interval(false_support, unsupported),
            "lexical_false_assurance_count": lexical_false_assurance,
            "confusion_matrix": confusion, "categories": summarise(by_category),
            "splits": summarise(by_split), "templates": summarise(by_template), "rows": rows,
            "disclaimer": "Fictional, rule- or hand-authored semantic labels; "
                          "not independent ground truth or clinical correctness."}
