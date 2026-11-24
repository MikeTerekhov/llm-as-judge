"""Fictional adversarial claim-evidence examples for evaluator stress testing.

Labels are hand-authored semantic expectations, NOT clinical ground truth.
"""
from dataclasses import dataclass
from enum import Enum
from .assessment import Claim
from .evidence_engine import EvidenceHit

class SemanticLabel(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT = "insufficient_evidence"

@dataclass(frozen=True)
class AdversarialExample:
    example_id: str
    category: str
    claim: Claim
    evidence: tuple[EvidenceHit, ...]
    expected: SemanticLabel
    explanation: str
    template: str = ""
    split: str = "core"

def _hit(identifier: str, excerpt: str) -> EvidenceHit:
    return EvidenceHit(identifier, "Fictional evidence", "https://example.org/synthetic",
                       "synthetic-v1", "2026-01-01", "2026-11-01T00:00:00+00:00",
                       "0"*64, excerpt, 1)

def adversarial_examples() -> tuple[AdversarialExample, ...]:
    """All examples concern invented objects, never patients or medical treatment."""
    rows = [
        ("negation-reversal", "negation", "The blue beacon is active.",
         "The blue beacon is not active.", SemanticLabel.CONTRADICTED,
         "The cited passage explicitly negates the claim."),
        ("negation-support", "negation", "The blue beacon is not active.",
         "The blue beacon is not active.", SemanticLabel.SUPPORTED,
         "The negative claim matches the cited statement."),
        ("quantity-mismatch", "quantity", "The test used seven widgets.",
         "The test used five widgets.", SemanticLabel.CONTRADICTED,
         "A different exact count is given."),
        ("quantity-support", "quantity", "The test used five widgets.",
         "The test used five widgets.", SemanticLabel.SUPPORTED,
         "The count and scope match."),
        ("hedged-certainty", "uncertainty", "The fictional sensor always succeeds.",
         "The fictional sensor may succeed.", SemanticLabel.INSUFFICIENT,
         "Possibility does not establish certainty."),
        ("scope-generalization", "scope", "All prototype units passed inspection.",
         "Three prototype units passed inspection.", SemanticLabel.INSUFFICIENT,
         "A subset cannot support a universal claim."),
        ("temporal-mismatch", "time", "The beacon was active on Monday.",
         "The beacon was active on Tuesday.", SemanticLabel.INSUFFICIENT,
         "The passage does not establish the Monday status."),
        ("temporal-support", "time", "The beacon was active on Tuesday.",
         "The beacon was active on Tuesday.", SemanticLabel.SUPPORTED,
         "The time qualifiers match."),
        ("entity-swap", "entity", "Module A passed the test.",
         "Module B passed the test.", SemanticLabel.INSUFFICIENT,
         "Evidence about B does not establish a claim about A."),
        ("entity-support", "entity", "Module B passed the test.",
         "Module B passed the test.", SemanticLabel.SUPPORTED,
         "The entity and predicate match."),
        ("causal-overreach", "causality", "The alarm caused the shutdown.",
         "The alarm sounded before the shutdown.", SemanticLabel.INSUFFICIENT,
         "Sequence alone does not establish causality."),
        ("causal-support", "causality", "The alarm caused the shutdown.",
         "The alarm caused the shutdown.", SemanticLabel.SUPPORTED,
         "The cited statement explicitly asserts causality."),
    ]
    examples = []
    for identifier, category, claim, excerpt, label, explanation in rows:
        doc_id = "SYN-ADV-" + identifier
        examples.append(AdversarialExample(identifier, category,
                        Claim(claim, (doc_id,)), (_hit(doc_id, excerpt),), label, explanation))
    return tuple(examples)
