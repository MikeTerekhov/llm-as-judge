import unittest
from clinical.benchmark_quality_gates import QualityThresholds, assess_quality
from clinical.adversarial_fixtures import adversarial_examples
from clinical.human_adjudication import make_review

class QualityGateTests(unittest.TestCase):
    def test_no_reviews_blocked(self):
        report = assess_quality(())
        self.assertEqual(report["status"], "blocked")
        self.assertIsNone(report["checks"][2]["observed"])

    def test_one_reviewer_blocked(self):
        reviews = (make_review("negation-reversal", "a", "contradicted"),)
        self.assertEqual(assess_quality(reviews)["status"], "blocked")

    def test_disagreement_blocks(self):
        reviews = (make_review("negation-reversal", "a", "contradicted"),
                   make_review("negation-reversal", "b", "supported"))
        report = assess_quality(reviews)
        self.assertFalse(next(x for x in report["checks"] if x["name"] == "dispute_fraction")["passed"])

    def test_complete_balanced_reviews_can_pass(self):
        labels = ["supported", "contradicted", "insufficient_evidence"]
        reviews = tuple(make_review(example.example_id, reviewer, labels[i % 3])
                        for i, example in enumerate(adversarial_examples())
                        for reviewer in ("a", "b"))
        report = assess_quality(reviews)
        self.assertEqual(report["status"], "pass")

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            QualityThresholds(min_review_coverage=1.5)

    def test_undefined_kappa_blocks_even_with_relaxed_threshold(self):
        reviews = tuple(make_review(example.example_id, reviewer, "supported")
                        for example in adversarial_examples()
                        for reviewer in ("a", "b"))
        report = assess_quality(reviews, QualityThresholds(min_pairwise_kappa=-1))
        self.assertEqual(report["status"], "blocked")

    def test_custom_policy(self):
        self.assertEqual(QualityThresholds(min_pairwise_kappa=0.8).min_pairwise_kappa, 0.8)

if __name__ == "__main__":
    unittest.main()
