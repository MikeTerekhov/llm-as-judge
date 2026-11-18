"""Run the synthetic benchmark without model calls or patient data."""
import json
from dataclasses import asdict
from clinical.assessment import Claim
from clinical.claim_judge import JudgeStatus
from clinical.evidence_engine import EvidenceHit
from clinical.judge_benchmark import BenchmarkExample, evaluate

def fixture():
    hit = EvidenceHit("SYN-REF", "Synthetic", "https://clinicalinfo.hiv.gov/en/guidelines",
                      "test", "2026-10-01", "2026-11-01T00:00:00+00:00",
                      "0" * 64, "Synthetic monitoring is described in the fixture.", 2)
    return (
        BenchmarkExample("overlap", Claim("Synthetic monitoring", ("SYN-REF",)), (hit,),
                         JudgeStatus.REVIEW_REQUIRED, "lexical_overlap"),
        BenchmarkExample("fabricated", Claim("Synthetic monitoring", ("FAKE",)), (hit,),
                         JudgeStatus.ABSTAIN, "fabricated_citation"),
        BenchmarkExample("unrelated", Claim("Synthetic unrelated result", ("SYN-REF",)), (hit,),
                         JudgeStatus.FLAGGED, "unsupported_terms"),
        BenchmarkExample("negation", Claim("Synthetic monitoring is not described in the fixture", ("SYN-REF",)), (hit,),
                         JudgeStatus.FLAGGED, "negation"),
        BenchmarkExample("missing", Claim("Synthetic monitoring", ()), (hit,),
                         JudgeStatus.ABSTAIN, "missing_citation"),
        BenchmarkExample("blank", Claim("", ("SYN-REF",)), (hit,),
                         JudgeStatus.ABSTAIN, "blank_claim"),
    )

if __name__ == "__main__":
    print(json.dumps(asdict(evaluate(fixture())), indent=2, sort_keys=True))
