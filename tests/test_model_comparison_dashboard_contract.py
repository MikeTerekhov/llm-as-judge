from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend/app/judge/model-comparison/page.tsx"

class ComparisonDashboardContractTests(unittest.TestCase):
    def test_local_only_upload_and_paired_results(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn('type="file"', source)
        self.assertIn("file.text()", source)
        self.assertIn("parseReport", source)
        self.assertIn("Fixture IDs or authored labels differ", source)
        self.assertIn("shared returned verdicts", source)
        self.assertNotIn("fetch(", source)

    def test_disclaimer_and_navigation(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn("not clinical accuracy", source)
        self.assertIn("No patient information", source)
        self.assertIn("Inspect disagreements", source)
        self.assertIn("Conditional label agreement", source)
        judge = (ROOT/"frontend/app/judge/page.tsx").read_text(encoding="utf-8")
        self.assertIn("/judge/model-comparison", judge)

if __name__ == "__main__":
    unittest.main()
