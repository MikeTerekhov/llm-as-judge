"""Research-only, deterministic assessment pipeline with evidence-grounding gates.

No regimen recommendations or clinical safety determinations are produced.
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Protocol

from .models import ClinicalCase
from .validation import review_case
from .evidence_engine import EvidenceHit, LocalEvidenceIndex


class AssessmentStatus(str, Enum):
    ABSTAIN = "abstain"
    EVIDENCE_REVIEW = "evidence_review"


@dataclass(frozen=True)
class Claim:
    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Assessment:
    case_id: str
    status: AssessmentStatus
    claims: tuple[Claim, ...]
    evidence: tuple[EvidenceHit, ...]
    warnings: tuple[str, ...]
    disclaimer: str = "Synthetic research only. Not validated for diagnosis, prescribing, or clinical care."


class ClaimGenerator(Protocol):
    def generate(self, case: ClinicalCase, evidence: tuple[EvidenceHit, ...]) -> tuple[Claim, ...]:
        """Untrusted model output; must pass citation and scope validation."""
        ...


class NoClaimsGenerator:
    def generate(self, case: ClinicalCase, evidence: tuple[EvidenceHit, ...]) -> tuple[Claim, ...]:
        return ()


def validate_claims(claims: tuple[Claim, ...], evidence: tuple[EvidenceHit, ...]) -> tuple[str, ...]:
    """Validate provenance references, not medical correctness or entailment."""
    known = {hit.document_id for hit in evidence}
    errors = []
    for i, claim in enumerate(claims):
        if not claim.text.strip():
            errors.append(f"Claim {i} is blank.")
        if not claim.evidence_ids or any(ref not in known for ref in claim.evidence_ids):
            errors.append(f"Claim {i} has missing or unknown citations.")
    return tuple(errors)


class AssessmentPipeline:
    def __init__(self, index: LocalEvidenceIndex, generator: ClaimGenerator | None = None):
        self.index = index
        self.generator = generator or NoClaimsGenerator()

    def assess(self, case: ClinicalCase, query: str, *, as_of: date | None = None) -> Assessment:
        review = review_case(case)
        if not review.ready_for_evidence_review:
            return Assessment(case.case_id, AssessmentStatus.ABSTAIN, (), (), review.warnings)
        evidence = tuple(self.index.search(query, as_of=as_of))
        if not evidence:
            return Assessment(case.case_id, AssessmentStatus.ABSTAIN, (), (),
                              ("No matching current evidence; abstain from assessment.",))
        # The generator is optional and untrusted. No automated clinical endorsement.
        try:
            claims = tuple(self.generator.generate(case, evidence))
            errors = validate_claims(claims, evidence)
        except Exception:
            return Assessment(case.case_id, AssessmentStatus.ABSTAIN, (), evidence,
                              ("Claim generation failed; abstain.",))
        if errors or not claims:
            return Assessment(case.case_id, AssessmentStatus.ABSTAIN, (), evidence,
                              errors or ("No substantiated claims supplied; abstain.",))
        # Citation existence is not clinical correctness: this status only queues review.
        return Assessment(case.case_id, AssessmentStatus.EVIDENCE_REVIEW, claims, evidence,
                          ("Citations verified by identifier only; clinician must verify claims against sources.",))
