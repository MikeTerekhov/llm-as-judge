import unittest
from copy import deepcopy
from clinical.adversarial_fixtures import adversarial_examples
from clinical.model_run_comparison import compare_runs

def sample(name, verdicts):
    examples = adversarial_examples()
    return {"mode":"executed","model":name,"report":{"total":12,"rows":[
        {"example_id":ex.example_id,"expected":ex.expected.value,
         "model_verdict":verdicts.get(ex.example_id)} for ex in examples]}}

class ModelRunComparisonTests(unittest.TestCase):
    def test_identical_complete_runs(self):
        verdicts = {ex.example_id:ex.expected.value for ex in adversarial_examples()}
        report = compare_runs([sample("a",verdicts),sample("b",verdicts)])
        self.assertEqual(report["pairs"][0]["shared_verdicts"],12)
        self.assertEqual(report["pairs"][0]["disagreement_rate"],0.0)
        self.assertEqual(report["runs"][0]["conditional_agreement"],1.0)

    def test_partial_coverage_not_mistaken_for_accuracy(self):
        examples = adversarial_examples()
        a = sample("a",{examples[0].example_id:examples[0].expected.value})
        b = sample("b",{examples[1].example_id:examples[1].expected.value})
        report = compare_runs([a,b])
        self.assertEqual(report["pairs"][0]["shared_verdicts"],0)
        self.assertIsNone(report["pairs"][0]["disagreement_rate"])
        self.assertEqual(report["runs"][0]["returned"],1)

    def test_rejects_mismatched_expected_labels(self):
        a,b = sample("a",{}),sample("b",{})
        b["report"]["rows"][0]["expected"]="supported" if b["report"]["rows"][0]["expected"]!="supported" else "contradicted"
        with self.assertRaises(ValueError):
            compare_runs([a,b])

    def test_rejects_duplicate_fixture(self):
        a=sample("a",{})
        a["report"]["rows"][1]["example_id"]=a["report"]["rows"][0]["example_id"]
        with self.assertRaises(ValueError):
            compare_runs([a,sample("b",{})])

    def test_dry_run_rejected(self):
        a=sample("a",{})
        a["mode"]="dry_run"
        with self.assertRaises(ValueError):
            compare_runs([a,sample("b",{})])

if __name__ == "__main__":
    unittest.main()
