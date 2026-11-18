import copy
import unittest
from clinical.human_adjudication import make_review
from clinical.reproducible_report import build_report, verify_report
from clinical.benchmark_quality_gates import QualityThresholds

class ReportTests(unittest.TestCase):
    def test_empty_review_report_is_blocked_and_verifiable(self):
        report = build_report(())
        self.assertEqual(report["fixture_count"], 12)
        self.assertEqual(report["quality_gates"]["status"], "blocked")
        self.assertTrue(verify_report(report))

    def test_deterministic_across_review_order_and_timestamps(self):
        a = make_review("negation-reversal", "reviewer_a", "contradicted", "private note")
        b = make_review("negation-reversal", "reviewer_b", "supported", "different note")
        first = build_report((a,b))
        second = build_report((b,a))
        self.assertEqual(first["report_sha256"], second["report_sha256"])

    def test_excludes_reviewer_ids_and_notes(self):
        review = make_review("negation-reversal", "secret_reviewer", "supported", "secret_note")
        report = build_report((review,))
        text = str(report)
        self.assertNotIn("secret_reviewer", text)
        self.assertNotIn("secret_note", text)

    def test_tampering_detected(self):
        report = build_report(())
        modified = copy.deepcopy(report)
        modified["fixture_count"] = 99
        self.assertFalse(verify_report(modified))

    def test_policy_changes_checksum(self):
        first = build_report(())
        second = build_report((), QualityThresholds(min_review_coverage=0.5))
        self.assertNotEqual(first["report_sha256"], second["report_sha256"])

    def test_invalid_experiment_id_rejected(self):
        with self.assertRaises(ValueError):
            build_report((), experiment_id="../../private")

    def test_experiment_metadata(self):
        report = build_report((), experiment_id="synthetic-run-1")
        self.assertEqual(report["experiment_id"], "synthetic-run-1")

if __name__ == "__main__":
    unittest.main()
