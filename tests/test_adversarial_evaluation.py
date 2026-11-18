import unittest
from clinical.adversarial_fixtures import adversarial_examples, SemanticLabel
from clinical.adversarial_evaluation import evaluate_adversarial
from api.adversarial_benchmark import adversarial

class AdversarialTests(unittest.TestCase):
    def test_dataset_has_twelve_cases(self):
        self.assertEqual(len(adversarial_examples()), 12)

    def test_categories_cover_critical_semantic_failures(self):
        categories = {x.category for x in adversarial_examples()}
        self.assertTrue({"negation","quantity","uncertainty","scope","time","entity","causality"} <= categories)

    def test_labels_are_semantic_not_lexical(self):
        examples = adversarial_examples()
        self.assertEqual(examples[0].expected, SemanticLabel.CONTRADICTED)
        self.assertEqual(examples[1].expected, SemanticLabel.SUPPORTED)

    def test_potential_false_assurance_detected(self):
        report = evaluate_adversarial(adversarial_examples())
        self.assertGreater(report["potential_false_assurance_count"], 0)

    def test_duplicate_ids_rejected(self):
        examples = adversarial_examples()
        with self.assertRaises(ValueError):
            evaluate_adversarial((examples[0], examples[0]))

    def test_api_is_static_and_offline(self):
        self.assertEqual(adversarial()["total"], 12)

if __name__ == "__main__":
    unittest.main()
