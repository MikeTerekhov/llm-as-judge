import json
import unittest
from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_model_benchmark import benchmark_adversarial
from api.adversarial_model_benchmark import adversarial_model

def mock_model(prompt):
    data = json.loads(prompt.split("DATA:\n", 1)[1])
    return json.dumps({"verdict": "supported", "rationale": "Synthetic mock.",
                       "citation_ids": [hit["document_id"] for hit in data["evidence"]]})

class AdversarialModelTests(unittest.TestCase):
    def test_default_has_no_model_results(self):
        report = benchmark_adversarial(adversarial_examples())
        self.assertEqual(report["total"], 12)
        self.assertEqual(report["model_returned"], 0)
        self.assertIsNone(report["label_agreement_rate"])

    def test_mock_model_returns_metrics(self):
        report = benchmark_adversarial(adversarial_examples(), mock_model)
        self.assertEqual(report["model_returned"], 12)
        self.assertIsNotNone(report["label_agreement_rate"])
        self.assertIn("negation", report["categories"])

    def test_category_counts(self):
        report = benchmark_adversarial(adversarial_examples())
        self.assertEqual(sum(x["examples"] for x in report["categories"].values()), 12)

    def test_duplicate_ids_rejected(self):
        example = adversarial_examples()[0]
        with self.assertRaises(ValueError):
            benchmark_adversarial((example, example))

    def test_endpoint_never_calls_model(self):
        self.assertEqual(adversarial_model()["model_abstained"], 12)

if __name__ == "__main__":
    unittest.main()
