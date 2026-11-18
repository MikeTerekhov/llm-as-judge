import unittest
from api.judge_dashboard import benchmark

class JudgeDashboardTests(unittest.TestCase):
    def test_demo_report_has_only_static_synthetic_cases(self):
        result = benchmark()
        self.assertEqual(result["summary"]["total"], 6)
        self.assertEqual(len(result["examples"]), 6)
        self.assertFalse(result["model_enabled"])

    def test_explanations_and_categories(self):
        result = benchmark()
        self.assertIn("negation", result["summary"]["per_category"])
        for example in result["examples"]:
            self.assertIn("reasons", example)
            self.assertIn("predicted", example)
            self.assertIn("lexical_coverage", example)

if __name__ == "__main__":
    unittest.main()
