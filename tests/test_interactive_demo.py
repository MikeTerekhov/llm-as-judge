"""Keep frontend demo examples synchronized with the canonical fictional benchmark."""
import json
import unittest
from pathlib import Path
from clinical.adversarial_fixtures import adversarial_examples

FIXTURES = Path(__file__).resolve().parents[1] / "frontend/app/demo/demo-fixtures.json"

class InteractiveDemoTests(unittest.TestCase):
    def test_demo_examples_match_canonical_fixtures(self):
        rows = json.loads(FIXTURES.read_text(encoding="utf-8"))
        canonical = {item.example_id: item for item in adversarial_examples()}
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        for row in rows:
            self.assertIn(row["id"], canonical)
            item = canonical[row["id"]]
            self.assertEqual(row["claim"], item.claim.text)
            self.assertEqual(row["evidence"], item.evidence[0].excerpt)
            self.assertEqual(row["expected"], item.expected.value)
            self.assertEqual(row["explanation"], item.explanation)

    def test_demo_is_nonclinical_and_does_not_contain_patient_data(self):
        rows = json.loads(FIXTURES.read_text(encoding="utf-8"))
        self.assertTrue(all(row["id"] and row["claim"] and row["evidence"] for row in rows))
        self.assertTrue(all("patient" not in row["claim"].lower() for row in rows))

if __name__ == "__main__":
    unittest.main()
