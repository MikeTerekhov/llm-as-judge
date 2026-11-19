import unittest
from clinical.semantic_metrics import classification_metrics
from clinical.adversarial_model_benchmark import benchmark_adversarial
from clinical.adversarial_fixtures import adversarial_examples

class SemanticMetricsTests(unittest.TestCase):
    def test_no_verdicts_means_no_accuracy(self):
        result = classification_metrics([{"expected":"supported","model_verdict":None}])
        self.assertIsNone(result["accuracy"])
        self.assertIsNone(result["macro_f1"])
        self.assertEqual(result["abstained"], 1)
        self.assertEqual(result["coverage"], 0.0)

    def test_perfect_predictions(self):
        result = classification_metrics([{"expected":label,"model_verdict":label}
                                         for label in ("supported","contradicted","insufficient_evidence")])
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["macro_f1"], 1.0)
        self.assertEqual(result["per_label"]["supported"]["precision"], 1.0)

    def test_mixed_predictions_and_abstention(self):
        result = classification_metrics([
            {"expected":"supported","model_verdict":"contradicted"},
            {"expected":"contradicted","model_verdict":"contradicted"},
            {"expected":"insufficient_evidence","model_verdict":None}])
        self.assertEqual(result["evaluated"], 2)
        self.assertEqual(result["abstained"], 1)
        self.assertEqual(result["accuracy"], 0.5)
        self.assertEqual(result["confusion"]["supported"]["contradicted"], 1)
        self.assertEqual(result["per_label"]["contradicted"]["precision"], 0.5)
        self.assertEqual(result["per_label"]["supported"]["recall"], 0.0)

    def test_unknown_verdict_rejected(self):
        with self.assertRaises(ValueError):
            classification_metrics([{"expected":"supported","model_verdict":"maybe"}])

    def test_benchmark_has_no_fake_accuracy_without_model(self):
        report = benchmark_adversarial(adversarial_examples())
        self.assertIsNone(report["classification"]["accuracy"])
        self.assertEqual(report["classification"]["abstained"], 12)

if __name__ == "__main__":
    unittest.main()
