"""Compare lexical screening with hand-authored semantic fixture expectations.

Lexical REVIEW_REQUIRED is not a semantic 'supported' verdict.
"""
from .adversarial_fixtures import AdversarialExample, SemanticLabel
from .claim_judge import JudgeStatus, judge_claim

def evaluate_adversarial(examples: tuple[AdversarialExample, ...]) -> dict:
    if not examples:
        raise ValueError("Dataset must not be empty")
    ids = [example.example_id for example in examples]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate example IDs")
    rows = []
    flagged = 0
    potential_false_assurance = 0
    for example in examples:
        screening = judge_claim(example.claim, example.evidence)
        if screening.status != JudgeStatus.REVIEW_REQUIRED:
            flagged += 1
        if (screening.status == JudgeStatus.REVIEW_REQUIRED
                and example.expected != SemanticLabel.SUPPORTED):
            potential_false_assurance += 1
        rows.append({"id": example.example_id, "category": example.category,
                     "expected_semantic_label": example.expected.value,
                     "lexical_status": screening.status.value,
                     "lexical_coverage": screening.lexical_coverage,
                     "potential_false_assurance": (screening.status == JudgeStatus.REVIEW_REQUIRED
                                                  and example.expected != SemanticLabel.SUPPORTED),
                     "explanation": example.explanation})
    return {"total": len(rows), "flagged_by_lexical_screen": flagged,
            "potential_false_assurance_count": potential_false_assurance,
            "examples": rows,
            "disclaimer": "Hand-authored fictional labels, not independent clinical ground truth."}
