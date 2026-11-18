import unittest
from clinical.assessment import Claim
from clinical.claim_judge import JudgeStatus
from clinical.evidence_engine import EvidenceHit
from clinical.judge_benchmark import BenchmarkExample, evaluate

HIT = EvidenceHit("SYN-REF", "Synthetic", "https://clinicalinfo.hiv.gov/en/guidelines",
                  "test", "2026-10-01", "2026-11-01T00:00:00+00:00",
                  "0"*64, "Synthetic monitoring is described in the fixture.", 2)

def fixture():
    return (
        BenchmarkExample("overlap", Claim("Synthetic monitoring", ("SYN-REF",)), (HIT,),
                         JudgeStatus.REVIEW_REQUIRED, "lexical_overlap"),
        BenchmarkExample("fabricated", Claim("Synthetic monitoring", ("FAKE",)), (HIT,),
                         JudgeStatus.ABSTAIN, "fabricated_citation"),
        BenchmarkExample("unrelated", Claim("Synthetic unrelated result", ("SYN-REF",)), (HIT,),
                         JudgeStatus.FLAGGED, "unsupported_terms"),
        BenchmarkExample("negation", Claim("Synthetic monitoring is not described in the fixture", ("SYN-REF",)), (HIT,),
                         JudgeStatus.FLAGGED, "negation"),
        BenchmarkExample("missing", Claim("Synthetic monitoring", ()), (HIT,),
                         JudgeStatus.ABSTAIN, "missing_citation"),
        BenchmarkExample("blank", Claim("", ("SYN-REF",)), (HIT,),
                         JudgeStatus.ABSTAIN, "blank_claim"),
    )

class BenchmarkTests(unittest.TestCase):
    def test_deterministic_baseline(self):
        result = evaluate(fixture())
        self.assertEqual(result.total, 6)
        self.assertEqual(result.correct, 6)
        self.assertEqual(result.accuracy, 1.0)

    def test_confusion_counts(self):
        result = evaluate(fixture())
        self.assertEqual(result.confusion["abstain"]["abstain"], 3)

    def test_reject_empty(self):
        with self.assertRaises(ValueError):
            evaluate(())

    def test_reject_duplicate_ids(self):
        with self.assertRaises(ValueError):
            evaluate((fixture()[0], fixture()[0]))

    def test_category_metrics(self):
        result = evaluate(fixture())
        self.assertEqual(result.per_category["negation"]["count"], 1)

if __name__ == "__main__":
    unittest.main()
