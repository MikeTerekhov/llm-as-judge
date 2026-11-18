import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.verify_evaluation_ci import generate, main
from clinical.reproducible_report import verify_report


class EvaluationCITests(unittest.TestCase):
    def test_generates_deterministic_report(self):
        self.assertEqual(generate(), generate())

    def test_integrity(self):
        self.assertTrue(verify_report(generate()))

    def test_empty_reviews_block_quality_gates(self):
        report = generate()
        self.assertEqual(report["review_count"], 0)
        self.assertEqual(report["quality_gates"]["status"], "blocked")

    def test_cli_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch("sys.argv", ["verify_evaluation_ci", "--output", str(output)]):
                main()
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(verify_report(report))
            self.assertEqual(report["fixture_count"], 12)


if __name__ == "__main__":
    unittest.main()
