import json
import unittest
from clinical.secure_model_runner import load_config, run_synthetic_comparison, RunnerConfig

ENV = {"AI_REGIMEN_ENABLE_MODEL_JUDGE": "true",
       "AI_REGIMEN_MODEL_ENDPOINT": "https://judge.example.org/v1/chat/completions",
       "AI_REGIMEN_MODEL_NAME": "synthetic-model",
       "AI_REGIMEN_MODEL_API_KEY": "test-secret",
       "AI_REGIMEN_MODEL_ALLOWED_HOST": "judge.example.org"}

class RunnerTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with self.assertRaises(ValueError):
            load_config({})

    def test_requires_exact_opt_in(self):
        with self.assertRaises(ValueError):
            load_config({**ENV, "AI_REGIMEN_ENABLE_MODEL_JUDGE": "1"})

    def test_rejects_non_allowlisted_host(self):
        with self.assertRaises(ValueError):
            load_config({**ENV, "AI_REGIMEN_MODEL_ALLOWED_HOST": "other.example.org"})

    def test_rejects_insecure_endpoint(self):
        with self.assertRaises(ValueError):
            load_config({**ENV, "AI_REGIMEN_MODEL_ENDPOINT": "http://judge.example.org/v1/chat/completions"})

    def test_rejects_url_credentials(self):
        with self.assertRaises(ValueError):
            load_config({**ENV, "AI_REGIMEN_MODEL_ENDPOINT": "https://user:pass@judge.example.org/v1/chat/completions"})

    def test_rejects_custom_port(self):
        with self.assertRaises(ValueError):
            load_config({**ENV, "AI_REGIMEN_MODEL_ENDPOINT": "https://judge.example.org:8443/v1/chat/completions"})

    def test_rejects_missing_api_key(self):
        with self.assertRaises(ValueError):
            load_config({**ENV, "AI_REGIMEN_MODEL_API_KEY": ""})

    def test_mock_transport_receives_only_synthetic_fixtures(self):
        seen = []
        def factory(**kwargs):
            self.assertEqual(kwargs["timeout"], 15)
            def call(prompt):
                data = json.loads(prompt.split("DATA:\\n", 1)[1])
                seen.append(data)
                return json.dumps({"verdict": "insufficient_evidence",
                                   "rationale": "Synthetic mock",
                                   "citation_ids": []})
            return call
        report = run_synthetic_comparison(load_config(ENV), transport_factory=factory)
        self.assertEqual(report.total, 6)
        self.assertGreater(len(seen), 0)
        self.assertTrue(all("case_id" not in data for data in seen))
        self.assertTrue(all("SYN-" in data["claim"] or not data["claim"] or
                            "Synthetic" in data["claim"] for data in seen))

if __name__ == "__main__":
    unittest.main()
