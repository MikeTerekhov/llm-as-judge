from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend/app/judge/experiment-history/page.tsx"

class ExperimentHistoryDashboardContractTests(unittest.TestCase):
    def test_local_only_history_import_and_visualization(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn('type="file"', source)
        self.assertIn("file.text()", source)
        self.assertIn("schema_version", source)
        self.assertIn("Agreement over time", source)
        self.assertIn("Filter model", source)
        self.assertIn("Inspect", source)
        self.assertNotIn("fetch(", source)

    def test_caveats_and_navigation(self):
        source = PAGE.read_text(encoding="utf-8")
        self.assertIn("not independent clinical accuracy", source)
        self.assertIn("not cryptographically verified", source)
        overview = (ROOT / "frontend/app/judge/overview/page.tsx").read_text(encoding="utf-8")
        self.assertIn("/judge/experiment-history", overview)

if __name__ == "__main__":
    unittest.main()
