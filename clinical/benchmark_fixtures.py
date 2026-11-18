"""Fictional, static examples for public demo benchmark. No patient records."""
from .assessment import Claim
from .claim_judge import JudgeStatus
from .evidence_engine import EvidenceHit
from .judge_benchmark import BenchmarkExample

def synthetic_examples() -> tuple[BenchmarkExample, ...]:
    hit = EvidenceHit("SYN-REF", "Synthetic demonstration", "https://clinicalinfo.hiv.gov/en/guidelines",
                      "fixture", "2026-10-01", "2026-11-01T00:00:00+00:00",
                      "0" * 64, "Synthetic monitoring is described in the fixture.", 2)
    def row(name, text, refs, expected, category):
        return BenchmarkExample(name, Claim(text, refs), (hit,), expected, category)
    return (
        row("overlap", "Synthetic monitoring", ("SYN-REF",), JudgeStatus.REVIEW_REQUIRED, "lexical_overlap"),
        row("fabricated", "Synthetic monitoring", ("FAKE",), JudgeStatus.ABSTAIN, "fabricated_citation"),
        row("unrelated", "Synthetic unrelated result", ("SYN-REF",), JudgeStatus.FLAGGED, "unsupported_terms"),
        row("negation", "Synthetic monitoring is not described in the fixture", ("SYN-REF",),
            JudgeStatus.FLAGGED, "negation"),
        row("missing", "Synthetic monitoring", (), JudgeStatus.ABSTAIN, "missing_citation"),
        row("blank", "", ("SYN-REF",), JudgeStatus.ABSTAIN, "blank_claim"),
    )
