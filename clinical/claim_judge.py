"""Deterministic, conservative claim-grounding screening for synthetic research.

Lexical coverage is NOT semantic entailment, clinical accuracy or LLM verification.
"""
from dataclasses import dataclass
from enum import Enum
import re

from .assessment import Claim
from .evidence_engine import EvidenceHit

TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset({"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
                       "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "with"})

class JudgeStatus(str, Enum):
    ABSTAIN = "abstain"
    FLAGGED = "flagged"
    REVIEW_REQUIRED = "review_required"

@dataclass(frozen=True)
class ClaimJudgment:
    claim_text: str
    status: JudgeStatus
    citation_ids: tuple[str, ...]
    lexical_coverage: float
    missing_terms: tuple[str, ...]
    reasons: tuple[str, ...]

def _terms(text: str) -> set[str]:
    return set(TOKEN.findall(text.lower())) - STOPWORDS

def judge_claim(claim: Claim, evidence: tuple[EvidenceHit, ...],
                *, min_coverage: float = 1.0) -> ClaimJudgment:
    """Never auto-approve a claim, even when all tokens occur in cited excerpts."""
    if not 0 < min_coverage <= 1:
        raise ValueError("min_coverage must be in (0, 1]")
    refs = {hit.document_id: hit for hit in evidence}
    cited = tuple(refs[key] for key in claim.evidence_ids if key in refs)
    reasons = []
    if not claim.text.strip():
        reasons.append("Blank claim.")
    if not claim.evidence_ids or len(cited) != len(claim.evidence_ids):
        reasons.append("Missing or unknown evidence citation.")
    if len(set(claim.evidence_ids)) != len(claim.evidence_ids):
        reasons.append("Duplicate citation identifiers.")
    terms = _terms(claim.text)
    if not terms:
        reasons.append("Claim has no meaningful terms.")
    source_terms = set().union(*(_terms(hit.excerpt) for hit in cited)) if cited else set()
    missing = tuple(sorted(terms - source_terms))
    coverage = len(terms & source_terms) / len(terms) if terms else 0.0
    if coverage < min_coverage:
        reasons.append("Claim vocabulary not fully present in cited excerpts.")
    if not cited or not terms:
        status = JudgeStatus.ABSTAIN
    elif reasons:
        status = JudgeStatus.FLAGGED
    else:
        status = JudgeStatus.REVIEW_REQUIRED
        reasons.append("Lexical match only; human review of meaning, negation and clinical context required.")
    return ClaimJudgment(claim.text, status, claim.evidence_ids, round(coverage, 4),
                         missing, tuple(reasons))

def judge_claims(claims: tuple[Claim, ...], evidence: tuple[EvidenceHit, ...],
                 *, min_coverage: float = 1.0) -> tuple[ClaimJudgment, ...]:
    return tuple(judge_claim(claim, evidence, min_coverage=min_coverage) for claim in claims)
