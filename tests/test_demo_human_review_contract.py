"""Human review demo must remain opt-in, read-only, and anonymous."""
import unittest
from pathlib import Path
from clinical.human_adjudication import adjudication_report

PAGE = Path(__file__).resolve().parents[1] / "frontend/app/demo/page.tsx"

class DemoHumanReviewTests(unittest.TestCase):
    def test_no_review_data_yields_unavailable_consensus(self):
        report = adjudication_report(())
        self.assertEqual(report["total_examples"], 12)
        self.assertEqual(report["reviewed_examples"], 0)
        self.assertIsNone(report["unanimity_rate"])
        self.assertTrue(all(row["needs_second_review"] for row in report["rows"]))

    def test_frontend_does_not_display_reviewer_ids(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn('fetch(API+"/api/v1/judge/adjudication"', source)
        self.assertIn("Load human review status", source)
        self.assertIn("Human review not enabled or unavailable", source)
        self.assertNotIn("reviewer_id", source)
        self.assertNotIn("reviewed_at", source)

if __name__ == "__main__":
    unittest.main()
