import copy
import unittest
from clinical.evaluation_regression import compare_reports
from clinical.release_manifest import build_manifest, verify_manifest
from scripts.verify_evaluation_ci import generate

SHA = "a" * 40

class ManifestTests(unittest.TestCase):
    def test_pending_blocked_report(self):
        report = generate()
        result = build_manifest(report, compare_reports(report, report), commit_sha=SHA,
                                recorded_at="2026-11-18T00:00:00+00:00")
        self.assertEqual(result["manual_review"]["decision"], "pending")
        self.assertEqual(result["readiness_status"], "blocked")
        self.assertTrue(verify_manifest(result))

    def test_approval_blocked_without_human_reviews(self):
        report = generate()
        with self.assertRaises(ValueError):
            build_manifest(report, compare_reports(report, report), commit_sha=SHA,
                           reviewer_id="reviewer1", approval="approved")

    def test_decision_requires_reviewer(self):
        with self.assertRaises(ValueError):
            build_manifest(generate(), None, commit_sha=SHA, approval="rejected")

    def test_reject_short_commit(self):
        with self.assertRaises(ValueError):
            build_manifest(generate(), None, commit_sha="abc")

    def test_detect_tampering(self):
        manifest = build_manifest(generate(), None, commit_sha=SHA)
        altered = copy.deepcopy(manifest)
        altered["manual_review"]["decision"] = "approved"
        self.assertFalse(verify_manifest(altered))

    def test_reject_naive_timestamp(self):
        with self.assertRaises(ValueError):
            build_manifest(generate(), None, commit_sha=SHA, recorded_at="2026-11-18T12:00:00")

    def test_reject_invalid_reviewer(self):
        with self.assertRaises(ValueError):
            build_manifest(generate(), None, commit_sha=SHA, reviewer_id="../escape")

if __name__ == "__main__":
    unittest.main()
