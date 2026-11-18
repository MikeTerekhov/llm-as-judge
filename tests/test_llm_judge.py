import json
import unittest
from clinical.assessment import Claim
from clinical.claim_judge import JudgeStatus
from clinical.evidence_engine import EvidenceHit
from clinical.llm_judge import evaluate_with_model, parse_judgment, build_prompt, ModelVerdict
from clinical.openai_compatible_judge import make_chat_transport

HIT = EvidenceHit("SYN-REF", "Synthetic", "https://clinicalinfo.hiv.gov/en/guidelines",
                  "test", "2026-10-01", "2026-11-01T00:00:00+00:00",
                  "0"*64, "Synthetic monitoring is described in the fixture.", 2)

def response(verdict="supported", ids=None):
    return json.dumps({"verdict": verdict, "rationale": "Synthetic test only.",
                       "citation_ids": ["SYN-REF"] if ids is None else ids})

class LLMJudgeTests(unittest.TestCase):
    def test_supported_still_requires_human_review(self):
        result = evaluate_with_model(Claim("Synthetic monitoring", ("SYN-REF",)), (HIT,),
                                     lambda prompt: response())
        self.assertEqual(result.disposition, "human_review_required")
        self.assertTrue(result.model.needs_human_review)

    def test_contradiction_flagged(self):
        result = evaluate_with_model(Claim("Synthetic monitoring", ("SYN-REF",)), (HIT,),
                                     lambda prompt: response("contradicted"))
        self.assertEqual(result.disposition, "flagged")

    def test_unknown_citation_abstains_without_model_call(self):
        def fail(prompt):
            raise AssertionError("Should not call model")
        result = evaluate_with_model(Claim("Synthetic monitoring", ("FAKE",)), (HIT,), fail)
        self.assertEqual(result.disposition, "abstain")

    def test_malformed_model_output_abstains(self):
        result = evaluate_with_model(Claim("Synthetic monitoring", ("SYN-REF",)), (HIT,),
                                     lambda prompt: "not json")
        self.assertEqual(result.disposition, "abstain")

    def test_fabricated_model_citation_rejected(self):
        with self.assertRaises(ValueError):
            parse_judgment(response(ids=["FAKE"]), {"SYN-REF"})

    def test_no_adapter_abstains(self):
        self.assertEqual(evaluate_with_model(Claim("Synthetic monitoring", ("SYN-REF",)),
                                             (HIT,)).disposition, "abstain")

    def test_prompt_contains_untrusted_data(self):
        prompt = build_prompt(Claim("Synthetic monitoring", ("SYN-REF",)), (HIT,))
        self.assertIn("DATA:", prompt)
        self.assertIn("SYN-REF", prompt)

    def test_http_requires_https(self):
        with self.assertRaises(ValueError):
            make_chat_transport(endpoint="http://localhost:1234/v1/chat/completions",
                                model="test", api_key="test")

if __name__ == "__main__":
    unittest.main()
