import json
import unittest
from unittest.mock import patch

from scripts.run_adversarial_model import run

def fake_transport(**kwargs):
    def call(prompt):
        payload = json.loads(prompt.split("DATA:\n", 1)[1])
        return json.dumps({"verdict":"supported","rationale":"Fictional test.",
                           "citation_ids":[hit["document_id"] for hit in payload["evidence"]]})
    return call

class ModelRunnerTests(unittest.TestCase):
    def test_dry_run_never_constructs_transport(self):
        with patch("scripts.run_adversarial_model.make_chat_transport",
                   side_effect=AssertionError("network must be off")):
            result = run(execute=False)
        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(result["network_calls"], 0)
        self.assertIsNone(result["report"]["classification"]["accuracy"])

    def test_execution_requires_explicit_configuration(self):
        with self.assertRaises(ValueError):
            run(execute=True)

    def test_opt_in_uses_injected_transport_and_real_metrics(self):
        with patch("scripts.run_adversarial_model.make_chat_transport",
                   side_effect=fake_transport) as adapter:
            result = run(execute=True,endpoint="https://api.example.org/v1/chat/completions",
                         model="fictional-model",api_key="dummy")
        adapter.assert_called_once()
        self.assertEqual(result["mode"], "executed")
        self.assertEqual(result["report"]["model_returned"], 12)
        self.assertEqual(result["report"]["classification"]["evaluated"], 12)
        self.assertEqual(result["report"]["classification"]["coverage"], 1.0)

if __name__ == "__main__":
    unittest.main()
