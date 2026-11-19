import unittest
from clinical.adversarial_fixtures import adversarial_examples
from clinical.experiment_manifest import build_manifest, verify_manifest

def sample_run():
    examples = adversarial_examples()
    return {"mode": "executed", "model": "fictional-model", "report": {"total": 12,
            "rows": [{"example_id": e.example_id, "expected": e.expected.value,
                      "model_verdict": e.expected.value} for e in examples]}}

class ExperimentManifestTests(unittest.TestCase):
    def test_manifest_verifies_original_report(self):
        run = sample_run()
        manifest = build_manifest(run, experiment_id="experiment-001",
                                  model_version="v1", recorded_at="2026-11-19T10:00:00+00:00")
        self.assertTrue(verify_manifest(manifest, run))
        self.assertEqual(manifest["fixture_count"], 12)

    def test_modified_verdict_detected(self):
        run = sample_run()
        manifest = build_manifest(run, experiment_id="experiment-001", model_version="v1")
        run["report"]["rows"][0]["model_verdict"] = None
        with self.assertRaisesRegex(ValueError, "checksum"):
            verify_manifest(manifest, run)

    def test_invalid_identifiers_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(sample_run(), experiment_id="../bad", model_version="v1")

    def test_missing_timezone_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(sample_run(), experiment_id="a", model_version="v1",
                           recorded_at="2026-11-19T10:00:00")

    def test_dry_run_rejected(self):
        run = sample_run()
        run["mode"] = "dry_run"
        with self.assertRaises(ValueError):
            build_manifest(run, experiment_id="a", model_version="v1")

    def test_wrong_model_rejected(self):
        run = sample_run()
        manifest = build_manifest(run, experiment_id="a", model_version="v1")
        manifest["model"] = "other"
        with self.assertRaises(ValueError):
            verify_manifest(manifest, run)

if __name__ == "__main__":
    unittest.main()
