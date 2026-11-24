import re
import unittest
from collections import Counter

from clinical.adversarial_evaluation import evaluate_adversarial
from clinical.adversarial_expanded import SCENARIOS, TEMPLATES, expanded_examples
from clinical.adversarial_fixtures import SemanticLabel, adversarial_examples
from clinical.semantic_benchmark import benchmark_semantic, wilson_interval
from tests.test_semantic_judge import stub_scorer

# Words that would suggest the fictional set has drifted toward real medical content.
CLINICAL_TERMS = re.compile(r"\b(patient|dose|mg|hiv|regimen|drug|therapy|treatment|"
                            r"diagnos\w*|prescri\w*|viral|cd4)\b", re.I)

class ExpandedDatasetTests(unittest.TestCase):
    def setUp(self):
        self.examples = expanded_examples()

    def test_size_and_split(self):
        self.assertEqual(len(self.examples), len(TEMPLATES) * len(SCENARIOS))
        self.assertGreaterEqual(len(self.examples), 300)
        splits = Counter(e.split for e in self.examples)
        self.assertEqual(splits["dev"] + splits["test"], len(self.examples))
        self.assertEqual(len(expanded_examples("dev")), splits["dev"])
        self.assertEqual(len(expanded_examples("test")), splits["test"])
        with self.assertRaises(ValueError):
            expanded_examples("train")

    def test_ids_unique_and_deterministic(self):
        ids = [e.example_id for e in self.examples]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(expanded_examples(), self.examples)

    def test_every_template_in_both_splits_with_one_label(self):
        for template_id, *_ in TEMPLATES:
            rows = [e for e in self.examples if e.template == template_id]
            self.assertEqual({e.split for e in rows}, {"dev", "test"})
            self.assertEqual(len({e.expected for e in rows}), 1)

    def test_scenarios_do_not_leak_across_splits(self):
        scenario_split = {}
        for e in self.examples:
            scenario = e.example_id.rsplit("-s", 1)[1]
            self.assertEqual(scenario_split.setdefault(scenario, e.split), e.split)

    def test_covers_core_categories_and_all_labels(self):
        core = {e.category for e in adversarial_examples()}
        self.assertTrue(core <= {e.category for e in self.examples})
        labels = Counter(e.expected for e in self.examples)
        self.assertEqual(set(labels), set(SemanticLabel))
        self.assertTrue(all(count >= 50 for count in labels.values()))

    def test_open_and_explicit_differences_are_paired(self):
        labels = {t[0]: t[2] for t in TEMPLATES}
        for base in ("scope-subset", "time-other", "ent-swap"):
            self.assertEqual(labels[base + "-open"], SemanticLabel.INSUFFICIENT)
            self.assertEqual(labels[base + "-explicit"], SemanticLabel.CONTRADICTED)

    def test_text_is_well_formed_and_fictional(self):
        for e in self.examples:
            for text in (e.claim.text, e.evidence[0].excerpt):
                self.assertRegex(text, r"^[A-Z].*\.$")
                self.assertNotIn("  ", text)
                self.assertIsNone(CLINICAL_TERMS.search(text), text)
            self.assertEqual(e.claim.evidence_ids, (e.evidence[0].document_id,))

    def test_core_dataset_unchanged(self):
        core = adversarial_examples()
        self.assertEqual(len(core), 12)
        self.assertTrue(all(e.split == "core" and e.template == "" for e in core))

class ExpandedBenchmarkTests(unittest.TestCase):
    def test_lexical_evaluation_runs(self):
        report = evaluate_adversarial(expanded_examples())
        self.assertEqual(report["total"], 360)
        self.assertGreater(report["potential_false_assurance_count"], 0)

    def test_semantic_report_groups(self):
        report = benchmark_semantic(expanded_examples(), stub_scorer, scorer_name="stub")
        self.assertEqual(set(report["splits"]), {"dev", "test"})
        self.assertEqual(len(report["templates"]), len(TEMPLATES))
        self.assertEqual(sum(t["examples"] for t in report["templates"].values()), 360)
        self.assertEqual(report["false_support_count"], 0)
        lo, hi = report["label_agreement_95ci"]
        self.assertLessEqual(lo, report["label_agreement_rate"])
        self.assertLessEqual(report["label_agreement_rate"], hi)
        neg = report["templates"]["neg-reversal"]
        self.assertEqual(neg["verdicts"]["contradicted"], 10)
        self.assertEqual(neg["lexical_false_assurance"], 10)

    def test_wilson_interval(self):
        self.assertIsNone(wilson_interval(0, 0))
        self.assertEqual(wilson_interval(0, 10)[0], 0.0)
        lo, hi = wilson_interval(9, 12)
        self.assertTrue(0.4 < lo < 0.75 < hi < 0.95)

if __name__ == "__main__":
    unittest.main()
