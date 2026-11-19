import json
import tempfile
import unittest
from pathlib import Path

from clinical.adversarial_fixtures import adversarial_examples
from clinical.experiment_history_store import append_run, history_summary, read_history

def fixture_run(model="model-a", verdict="supported"):
    examples = adversarial_examples()
    return {"mode": "executed", "model": model,
            "report": {"total": len(examples), "rows": [
                {"example_id": e.example_id, "expected": e.expected.value,
                 "model_verdict": verdict} for e in examples]}}

class ExperimentHistoryStoreTests(unittest.TestCase):
    def test_save_reload_and_chronological_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"history.json"
            append_run(path, fixture_run("later"), recorded_at="2026-11-20T10:00:00+00:00")
            append_run(path, fixture_run("earlier"), recorded_at="2026-11-19T10:00:00+00:00")
            rows = history_summary(read_history(path))
            self.assertEqual([r["model"] for r in rows], ["earlier", "later"])
            self.assertEqual(rows[0]["returned"], 12)
            self.assertTrue(path.exists())

    def test_rejects_duplicate_without_mutating_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"history.json"
            run = fixture_run()
            append_run(path, run)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "already saved"):
                append_run(path, run)
            self.assertEqual(path.read_bytes(), before)

    def test_rejects_wrong_fixture_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = fixture_run()
            run["report"]["rows"][0]["expected"] = "supported" if run["report"]["rows"][0]["expected"] != "supported" else "contradicted"
            with self.assertRaises(ValueError):
                append_run(Path(tmp)/"history.json", run)

    def test_checksum_tampering_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"history.json"
            append_run(path, fixture_run())
            payload = json.loads(path.read_text())
            payload["runs"][0]["run"]["model"] = "tampered"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "checksum"):
                read_history(path)

    def test_no_history_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_history(Path(tmp)/"missing.json"), [])

    def test_dry_run_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = fixture_run()
            run["mode"] = "dry_run"
            with self.assertRaises(ValueError):
                append_run(Path(tmp)/"history.json", run)

if __name__ == "__main__":
    unittest.main()
