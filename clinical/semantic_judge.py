"""Sentence-level NLI screening for synthetic research claims.

An NLI model estimates whether one cited sentence entails or contradicts a claim.
That is a statistical text-inference signal, NOT clinical validation. A
"supported" verdict never approves a claim; it still requires human review.
"""
from dataclasses import dataclass
from math import isclose, isfinite
from typing import Callable
import re

from .assessment import Claim
from .claim_judge import JudgeStatus, judge_claim
from .evidence_engine import EvidenceHit
from .llm_judge import ModelVerdict

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?;])\s+")
MAX_SENTENCES_PER_EXCERPT = 50
MAX_SENTENCE_CHARS = 1000
MAX_CLAIM_CHARS = 1000

@dataclass(frozen=True)
class NLIScores:
    entailment: float
    neutral: float
    contradiction: float

    def __post_init__(self):
        values = (self.entailment, self.neutral, self.contradiction)
        if not all(isinstance(v, (int, float)) and isfinite(v) and 0 <= v <= 1 for v in values):
            raise ValueError("NLI scores must be finite probabilities in [0, 1]")
        if not isclose(sum(values), 1.0, abs_tol=1e-3):
            raise ValueError("NLI scores must sum to 1")

NLIScorer = Callable[[str, str], NLIScores]
"""Called as scorer(premise, hypothesis): premise is evidence, hypothesis is the claim."""

@dataclass(frozen=True)
class SentenceScore:
    document_id: str
    sentence: str
    scores: NLIScores

@dataclass(frozen=True)
class SemanticJudgment:
    claim_text: str
    lexical_status: JudgeStatus
    verdict: ModelVerdict | None
    disposition: str
    best_support: SentenceScore | None
    strongest_conflict: SentenceScore | None
    reasons: tuple[str, ...]
    needs_human_review: bool = True

def split_sentences(text: str) -> tuple[str, ...]:
    parts = (part.strip() for part in SENTENCE_BOUNDARY.split(text))
    sentences = tuple(part[:MAX_SENTENCE_CHARS] for part in parts if part)
    return sentences[:MAX_SENTENCES_PER_EXCERPT]

def _check_threshold(name: str, value: float) -> None:
    if not 0.5 < value <= 1:
        raise ValueError(f"{name} must be in (0.5, 1]")

def judge_claim_semantic(claim: Claim, evidence: tuple[EvidenceHit, ...],
                         scorer: NLIScorer | None, *, support_threshold: float = 0.9,
                         contradiction_threshold: float = 0.9) -> SemanticJudgment:
    """Score the claim against each cited sentence and combine with lexical screening.

    Contradiction takes precedence over support: conflicting cited evidence is flagged.
    Support requires a single sentence to entail the whole claim; claims that need
    several sentences combined are reported as insufficient rather than guessed at.
    """
    _check_threshold("support_threshold", support_threshold)
    _check_threshold("contradiction_threshold", contradiction_threshold)
    lexical = judge_claim(claim, evidence)

    def result(verdict, disposition, support, conflict, *reasons):
        return SemanticJudgment(claim.text, lexical.status, verdict, disposition,
                                support, conflict, tuple(reasons))

    if lexical.status == JudgeStatus.ABSTAIN:
        return result(None, "abstain", None, None, "Missing claim content or valid citations.")
    if scorer is None:
        return result(None, "abstain", None, None, "No NLI scorer configured.")
    cited = tuple(hit for hit in evidence if hit.document_id in claim.evidence_ids)
    hypothesis = claim.text.strip()[:MAX_CLAIM_CHARS]
    scored: list[SentenceScore] = []
    try:
        for hit in cited:
            for sentence in split_sentences(hit.excerpt):
                scores = scorer(sentence, hypothesis)
                if not isinstance(scores, NLIScores):
                    raise TypeError("Scorer must return NLIScores")
                scored.append(SentenceScore(hit.document_id, sentence, scores))
    except Exception:
        return result(None, "abstain", None, None, "NLI scoring failed or returned invalid output.")
    if not scored:
        return result(None, "abstain", None, None, "Cited excerpts contain no sentences.")

    support = max(scored, key=lambda s: s.scores.entailment)
    conflict = max(scored, key=lambda s: s.scores.contradiction)
    if conflict.scores.contradiction >= contradiction_threshold:
        reasons = ["A cited sentence contradicts the claim."]
        if support.scores.entailment >= support_threshold:
            reasons.append("Other cited text appears to support it; the evidence conflicts.")
        return result(ModelVerdict.CONTRADICTED, "flagged", support, conflict, *reasons)
    if support.scores.entailment < support_threshold:
        return result(ModelVerdict.INSUFFICIENT, "flagged", support, conflict,
                      "No single cited sentence entails the claim.")
    if lexical.status != JudgeStatus.REVIEW_REQUIRED:
        return result(ModelVerdict.SUPPORTED, "flagged", support, conflict,
                      "NLI suggests support but lexical screening flagged the claim; "
                      "manual review required.")
    return result(ModelVerdict.SUPPORTED, "human_review_required", support, conflict,
                  "NLI entailment is not clinical or semantic validation; "
                  "human review of meaning and context required.")

def judge_claims_semantic(claims: tuple[Claim, ...], evidence: tuple[EvidenceHit, ...],
                          scorer: NLIScorer | None, **thresholds) -> tuple[SemanticJudgment, ...]:
    return tuple(judge_claim_semantic(claim, evidence, scorer, **thresholds) for claim in claims)
