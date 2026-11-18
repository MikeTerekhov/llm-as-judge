import copy
import unittest
from clinical.evaluation_regression import compare_reports
from clinical.reproducible_report import build_report
from scripts.verify_evaluation_ci import generate

def reseal(report):
    from hashlib import sha256
    import json
    report["report_sha256"] = sha256(json.dumps(
        {k:v for k,v in report.items() if k != "report_sha256"},
        sort_keys=True, separators=(",",":"), ensure_ascii=True,
        allow_nan=False).encode("utf-8")).hexdigest()
    return report

class RegressionTests(unittest.TestCase):
    def test_identical_reports_pass(self):
        self.assertEqual(compare_reports(generate(), generate())["status"], "pass")

    def test_tampered_report_rejected(self):
        changed = copy.deepcopy(generate())
        changed["fixture_count"] = 999
        with self.assertRaises(ValueError):
            compare_reports(generate(), changed)

    def test_fixture_fingerprint_change_blocks(self):
        changed = copy.deepcopy(generate())
        changed["dataset_sha256"] = "f"*64
        reseal(changed)
        self.assertEqual(compare_reports(generate(), changed)["status"], "blocked")

    def test_allow_fixture_changes_is_explicit(self):
        changed = copy.deepcopy(generate())
        changed["dataset_sha256"] = "f"*64
        reseal(changed)
        self.assertEqual(compare_reports(generate(), changed, allow_fixture_changes=True)["status"], "pass")

    def test_evaluator_outcome_change_blocks(self):
        changed = copy.deepcopy(generate())
        changed["lexical_benchmark"]["examples"][0]["lexical_status"] = "flagged"
        reseal(changed)
        result = compare_reports(generate(), changed)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["changed_examples"][0]["change"], "evaluation_changed")

    def test_review_counts_change_reported(self):
        changed = copy.deepcopy(generate())
        changed["review_label_counts_sha256"] = "e"*64
        reseal(changed)
        result = compare_reports(generate(), changed)
        self.assertTrue(result["review_counts_changed"])
        self.assertEqual(result["status"], "pass")

if __name__ == "__main__":
    unittest.main()
