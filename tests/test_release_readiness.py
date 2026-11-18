import copy
import unittest
from clinical.release_readiness import assess_release
from clinical.evaluation_regression import compare_reports
from scripts.verify_evaluation_ci import generate

class ReadinessTests(unittest.TestCase):
    def test_missing_regression_blocks(self):
        result = assess_release(generate())
        self.assertIn("regression_comparison_missing", result["blockers"])

    def test_synthetic_ci_quality_blocks(self):
        report = generate()
        result = assess_release(report, compare_reports(report, report))
        self.assertIn("human_review_quality_blocked", result["blockers"])

    def test_tampered_report_blocks(self):
        report = copy.deepcopy(generate())
        report["fixture_count"] = 999
        self.assertEqual(assess_release(report)["blockers"], ["report_integrity_failed"])

    def test_wrong_regression_target_blocks(self):
        report = generate()
        regression = compare_reports(report, report)
        regression["current_sha256"] = "a"*64
        result = assess_release(report, regression)
        self.assertIn("regression_comparison_failed", result["blockers"])

    def test_relaxed_missing_regression_does_not_override_quality(self):
        result = assess_release(generate(), regression_required=False)
        self.assertEqual(result["status"], "blocked")

    def test_regression_pass_but_review_blocked(self):
        report = generate()
        result = assess_release(report, compare_reports(report, report))
        self.assertTrue(next(c for c in result["checks"]
                             if c["name"] == "regression_comparison")["passed"])
        self.assertEqual(result["status"], "blocked")

if __name__ == "__main__":
    unittest.main()
