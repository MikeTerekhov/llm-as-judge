"""Smoke checks for safe, read-only model comparison in the demo."""
import unittest
from pathlib import Path
from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_model_benchmark import benchmark_adversarial

PAGE = Path(__file__).resolve().parents[1] / "frontend/app/demo/page.tsx"

class DemoComparisonTests(unittest.TestCase):
    def test_no_model_by_default(self):
        report = benchmark_adversarial(adversarial_examples())
        self.assertEqual(report["total"], 12)
        self.assertEqual(report["model_returned"], 0)
        self.assertTrue(all(row["model_verdict"] is None for row in report["rows"]))

    def test_frontend_marks_absent_model_verdicts(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn('fetch(API+"/api/v1/judge/adversarial-model"', source)
        self.assertIn('"Not run"', source)
        self.assertIn("No external model is run by this page", source)
        self.assertIn("model_verdicts_returned", source)

if __name__ == "__main__":
    unittest.main()
