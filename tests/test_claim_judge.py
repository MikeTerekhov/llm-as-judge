import unittest
from clinical.assessment import Claim
from clinical.claim_judge import JudgeStatus, judge_claim, judge_claims
from clinical.evidence_engine import EvidenceHit

HIT = EvidenceHit("SYN-DOC", "Fixture", "https://clinicalinfo.hiv.gov/en/guidelines",
                  "test", "2026-10-01", "2026-11-01T00:00:00+00:00",
                  "a" * 64, "Synthetic monitoring is described in the fixture.", 2)

class ClaimJudgeTests(unittest.TestCase):
    def test_full_lexical_overlap_still_requires_review(self):
        result = judge_claim(Claim("Synthetic monitoring", ("SYN-DOC",)), (HIT,))
        self.assertEqual(result.status, JudgeStatus.REVIEW_REQUIRED)
        self.assertEqual(result.lexical_coverage, 1.0)

    def test_unknown_citation_abstains(self):
        result = judge_claim(Claim("Synthetic monitoring", ("UNKNOWN",)), (HIT,))
        self.assertEqual(result.status, JudgeStatus.ABSTAIN)

    def test_unsupported_vocabulary_flagged(self):
        result = judge_claim(Claim("Synthetic unrelated result", ("SYN-DOC",)), (HIT,))
        self.assertEqual(result.status, JudgeStatus.FLAGGED)
        self.assertIn("unrelated", result.missing_terms)

    def test_blank_claim_abstains(self):
        self.assertEqual(judge_claim(Claim(" ", ("SYN-DOC",)), (HIT,)).status, JudgeStatus.ABSTAIN)

    def test_negation_not_semantically_verified(self):
        result = judge_claim(Claim("Synthetic monitoring is not described in the fixture", ("SYN-DOC",)), (HIT,))
        self.assertNotEqual(result.status, JudgeStatus.REVIEW_REQUIRED)

    def test_duplicate_citation_flagged(self):
        result = judge_claim(Claim("Synthetic monitoring", ("SYN-DOC", "SYN-DOC")), (HIT,))
        self.assertEqual(result.status, JudgeStatus.FLAGGED)

    def test_batch(self):
        results = judge_claims((Claim("Synthetic monitoring", ("SYN-DOC",)),), (HIT,))
        self.assertEqual(len(results), 1)

if __name__ == "__main__":
    unittest.main()
