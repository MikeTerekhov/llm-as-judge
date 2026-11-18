import json
import unittest
from clinical.benchmark_fixtures import synthetic_examples
from clinical.model_comparison import compare
from api.judge_comparison import comparison

def mock_model(prompt):
    payload = json.loads(prompt.split("DATA:\n", 1)[1])
    ids = [hit["document_id"] for hit in payload["evidence"]]
    return json.dumps({"verdict": "supported", "rationale": "Synthetic mock only",
                       "citation_ids": ids})

class ComparisonTests(unittest.TestCase):
    def test_no_adapter_never_reports_zero_disagreement(self):
        report = compare(synthetic_examples())
        self.assertEqual(report.model_returned, 0)
        self.assertIsNone(report.disagreement_rate)
        self.assertTrue(all(row.model_verdict is None for row in report.rows))

    def test_mock_model_counts_disagreement(self):
        report = compare(synthetic_examples(), mock_model)
        self.assertGreater(report.model_returned, 0)
        self.assertIsNotNone(report.disagreement_rate)
        self.assertGreaterEqual(report.disagreement_count, 0)

    def test_endpoint_is_offline(self):
        result = comparison()
        self.assertFalse(result["model_enabled"])
        self.assertIsNone(result["disagreement_rate"])

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            compare(())

if __name__ == "__main__":
    unittest.main()
