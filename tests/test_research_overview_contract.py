"""Ensure research overview remains read-only and clearly marks unavailable data."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend/app/judge/overview/page.tsx"
README = ROOT / "README.md"

class ResearchOverviewTests(unittest.TestCase):
    def test_dashboard_uses_existing_read_only_routes(self):
        source = PAGE.read_text(encoding="utf-8")
        for route in ("/api/v1/judge/adversarial", "/api/v1/judge/adversarial-model",
                      "/api/v1/judge/adjudication", "/api/v1/judge/quality-gates"):
            self.assertIn(route, source)
        self.assertIn('cache:"no-store"', source)
        self.assertIn("Unavailable / disabled", source)
        self.assertIn("No diagnosis", source)
        self.assertNotIn('method:"POST"', source)

    def test_readme_documents_current_application(self):
        text = README.read_text(encoding="utf-8")
        for term in ("AI Regimen", "/judge/overview", "/demo", "requirements-api.txt",
                     "npm run build", "No real patient data"):
            self.assertIn(term, text)

if __name__ == "__main__":
    unittest.main()
