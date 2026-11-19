"""Smoke checks for offline demo export, complementing Next.js compilation."""
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "frontend/app/demo/page.tsx"

class DemoExportContractTests(unittest.TestCase):
    def test_export_uses_local_browser_download_only(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn("function exportResults()", source)
        self.assertIn('new Blob([JSON.stringify(report,null,2)]', source)
        self.assertIn('link.download="ai-regimen-demo-results.json"', source)
        self.assertIn("URL.revokeObjectURL(url)", source)

    def test_report_contains_disclaimers_and_per_fixture_results(self):
        source = PAGE.read_text(encoding="utf-8")
        for term in ("fixture_id", "participant_answer", "matches_author_label",
                     "explanation_revealed", "limitations", "No live LLM"):
            self.assertIn(term, source)

if __name__ == "__main__":
    unittest.main()
