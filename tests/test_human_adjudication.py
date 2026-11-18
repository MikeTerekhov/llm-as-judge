import tempfile
import unittest
from pathlib import Path
from clinical.human_adjudication import make_review, append_review, read_reviews, adjudication_report

class AdjudicationTests(unittest.TestCase):
    def test_valid_review(self):
        review = make_review("negation-reversal", "reviewer_1", "contradicted")
        self.assertEqual(review.label, "contradicted")

    def test_reject_unknown_case(self):
        with self.assertRaises(ValueError):
            make_review("real-patient", "reviewer_1", "supported")

    def test_reject_invalid_label(self):
        with self.assertRaises(ValueError):
            make_review("negation-reversal", "reviewer_1", "clinically_correct")

    def test_roundtrip_and_duplicate_prevention(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "reviews.jsonl"
            review = make_review("negation-reversal", "reviewer_1", "contradicted")
            append_review(path, review)
            self.assertEqual(len(read_reviews(path)), 1)
            with self.assertRaises(ValueError):
                append_review(path, review)

    def test_agreement(self):
        a = make_review("negation-reversal", "a", "contradicted")
        b = make_review("negation-reversal", "b", "contradicted")
        result = adjudication_report((a,b))
        self.assertEqual(result["unanimity_rate"], 1.0)

    def test_dispute(self):
        a = make_review("negation-reversal", "a", "contradicted")
        b = make_review("negation-reversal", "b", "supported")
        result = adjudication_report((a,b))
        self.assertTrue(result["rows"][0]["disputed"])

    def test_no_reviews_null_rate(self):
        self.assertIsNone(adjudication_report(())["unanimity_rate"])

if __name__ == "__main__":
    unittest.main()
