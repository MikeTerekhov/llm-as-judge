import importlib.util
import unittest

from clinical.adversarial_evaluation import evaluate_adversarial
from clinical.adversarial_fixtures import adversarial_examples, _hit
from clinical.assessment import Claim
from clinical.claim_judge import JudgeStatus
from clinical.llm_judge import ModelVerdict
from clinical.nli_backends import label_indices, make_transformers_nli
from clinical.semantic_benchmark import benchmark_semantic
from clinical.semantic_judge import NLIScores, judge_claim_semantic, split_sentences

ENTAIL = NLIScores(0.97, 0.02, 0.01)
NEUTRAL = NLIScores(0.05, 0.9, 0.05)
CONTRADICT = NLIScores(0.01, 0.02, 0.97)

def _norm(text):
    return text.lower().rstrip(".").strip()

def stub_scorer(premise, hypothesis):
    """Deterministic stand-in: identical sentences entail, a lone 'not' contradicts."""
    p, h = _norm(premise), _norm(hypothesis)
    if p == h:
        return ENTAIL
    if p.replace(" not ", " ") == h.replace(" not ", " "):
        return CONTRADICT
    return NEUTRAL

class SentenceTests(unittest.TestCase):
    def test_split_sentences(self):
        self.assertEqual(split_sentences("A is on. B is off!  C?"), ("A is on.", "B is off!", "C?"))
        self.assertEqual(split_sentences("   "), ())

    def test_scores_validated(self):
        for bad in [(0.5, 0.5, 0.5), (-0.1, 0.6, 0.5), (float("nan"), 0.5, 0.5)]:
            with self.assertRaises(ValueError):
                NLIScores(*bad)

class SemanticJudgeTests(unittest.TestCase):
    def setUp(self):
        self.hit = _hit("SYN-1", "The red lamp is on. The gate is closed.")

    def judge(self, text, evidence=None, scorer=stub_scorer, ids=("SYN-1",), **kw):
        return judge_claim_semantic(Claim(text, ids), evidence or (self.hit,), scorer, **kw)

    def test_supported_still_requires_human_review(self):
        result = self.judge("The gate is closed.")
        self.assertEqual(result.verdict, ModelVerdict.SUPPORTED)
        self.assertEqual(result.disposition, "human_review_required")
        self.assertTrue(result.needs_human_review)
        self.assertEqual(result.best_support.sentence, "The gate is closed.")
        self.assertEqual(result.best_support.document_id, "SYN-1")

    def test_negation_is_contradicted_despite_full_lexical_overlap(self):
        # Every claim word appears in the excerpt, so lexical screening passes it.
        hit = _hit("SYN-1", "The gate is not open. The gate is closed.")
        result = self.judge("The gate is not closed.", (hit,))
        self.assertEqual(result.lexical_status, JudgeStatus.REVIEW_REQUIRED)
        self.assertEqual(result.verdict, ModelVerdict.CONTRADICTED)
        self.assertEqual(result.strongest_conflict.sentence, "The gate is closed.")
        self.assertEqual(result.disposition, "flagged")

    def test_contradiction_takes_precedence_over_support(self):
        hit = _hit("SYN-1", "The gate is closed. The gate is not closed.")
        result = self.judge("The gate is closed.", (hit,))
        self.assertEqual(result.verdict, ModelVerdict.CONTRADICTED)
        self.assertIn("conflicts", " ".join(result.reasons))

    def test_neutral_evidence_is_insufficient(self):
        result = self.judge("The red lamp is closed.")
        self.assertEqual(result.verdict, ModelVerdict.INSUFFICIENT)
        self.assertEqual(result.disposition, "flagged")

    def test_nli_support_with_lexical_flag_stays_flagged(self):
        result = self.judge("The portal is shut.", scorer=lambda p, h: ENTAIL)
        self.assertEqual(result.lexical_status, JudgeStatus.FLAGGED)
        self.assertEqual(result.verdict, ModelVerdict.SUPPORTED)
        self.assertEqual(result.disposition, "flagged")

    def test_abstains_without_valid_citation(self):
        result = self.judge("The gate is closed.", ids=("UNKNOWN",))
        self.assertEqual(result.disposition, "abstain")
        self.assertIsNone(result.verdict)

    def test_abstains_without_scorer(self):
        self.assertEqual(self.judge("The gate is closed.", scorer=None).disposition, "abstain")

    def test_abstains_when_scorer_fails_or_misbehaves(self):
        def boom(p, h):
            raise RuntimeError("model crashed")
        for scorer in (boom, lambda p, h: {"entailment": 1.0}):
            result = self.judge("The gate is closed.", scorer=scorer)
            self.assertEqual(result.disposition, "abstain")
            self.assertIsNone(result.verdict)

    def test_thresholds_validated(self):
        for bad in (0.5, 0.0, 1.5):
            with self.assertRaises(ValueError):
                self.judge("The gate is closed.", support_threshold=bad)

    def test_threshold_controls_support(self):
        weak = NLIScores(0.8, 0.15, 0.05)
        scorer = lambda p, h: weak
        self.assertEqual(self.judge("The gate is closed.", scorer=scorer).verdict,
                         ModelVerdict.INSUFFICIENT)
        self.assertEqual(self.judge("The gate is closed.", scorer=scorer,
                                    support_threshold=0.75).verdict, ModelVerdict.SUPPORTED)

class SemanticBenchmarkTests(unittest.TestCase):
    def test_stub_benchmark_report(self):
        report = benchmark_semantic(adversarial_examples(), stub_scorer, scorer_name="stub")
        self.assertEqual(report["total"], 12)
        self.assertEqual(report["nli_returned"], 12)
        self.assertEqual(report["false_support_count"], 0)
        self.assertEqual(sum(sum(row.values()) for row in report["confusion_matrix"].values()), 12)
        self.assertEqual(report["lexical_false_assurance_count"],
                         evaluate_adversarial(adversarial_examples())["potential_false_assurance_count"])
        rows = {row["id"]: row for row in report["rows"]}
        self.assertEqual(rows["negation-reversal"]["nli_verdict"], "contradicted")
        self.assertTrue(rows["negation-support"]["matches_hand_authored_label"])

    def test_false_support_counted(self):
        report = benchmark_semantic(adversarial_examples(), lambda p, h: ENTAIL)
        unsupported = sum(e.expected.value != "supported" for e in adversarial_examples())
        self.assertEqual(report["false_support_count"], unsupported)

    def test_unconfigured_scorer_abstains(self):
        report = benchmark_semantic(adversarial_examples(), None)
        self.assertEqual(report["nli_returned"], 0)
        self.assertIsNone(report["label_agreement_rate"])

    def test_rejects_empty_and_duplicates(self):
        examples = adversarial_examples()
        with self.assertRaises(ValueError):
            benchmark_semantic((), stub_scorer)
        with self.assertRaises(ValueError):
            benchmark_semantic((examples[0], examples[0]), stub_scorer)

class BackendTests(unittest.TestCase):
    def test_label_indices(self):
        self.assertEqual(label_indices({0: "CONTRADICTION", 1: "Entailment", 2: "neutral"}),
                         {"contradiction": 0, "entailment": 1, "neutral": 2})
        for bad in ({0: "entailment", 1: "neutral"},
                    {0: "entailment", 1: "neutral", 2: "contradiction", 3: "other"},
                    {0: "entailment", 1: "entailment", 2: "contradiction"},
                    {0: "LABEL_0", 1: "LABEL_1", 2: "LABEL_2"}):
            with self.assertRaises(ValueError):
                label_indices(bad)

    @unittest.skipIf(importlib.util.find_spec("transformers"), "transformers installed")
    def test_missing_dependency_is_explained(self):
        with self.assertRaises(RuntimeError):
            make_transformers_nli()

if __name__ == "__main__":
    unittest.main()
