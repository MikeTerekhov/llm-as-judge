"""Verify the live demo uses the existing static synthetic endpoint."""
import unittest
from pathlib import Path
from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_evaluation import evaluate_adversarial

PAGE = Path(__file__).resolve().parents[1] / "frontend/app/demo/page.tsx"

class LiveDemoContractTests(unittest.TestCase):
    def test_live_route_is_static_and_read_only(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn('fetch(API+"/api/v1/judge/adversarial"', source)
        self.assertIn('cache:"no-store"', source)
        self.assertIn('setLiveStatus("error")', source)
        self.assertIn('Use offline example', source)

    def test_real_fixture_report_is_deterministic(self):
        first = evaluate_adversarial(adversarial_examples())
        second = evaluate_adversarial(adversarial_examples())
        self.assertEqual(first, second)
        self.assertEqual(first["total"], 12)
        self.assertEqual(len(first["examples"]), 12)

    def test_demo_does_not_claim_live_llm(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn("No external LLM was invoked", source)
        self.assertIn("Actual deterministic lexical screener", source)

if __name__ == "__main__":
    unittest.main()
