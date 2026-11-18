import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from clinical.benchmark_fixtures import synthetic_examples
from clinical.model_comparison import compare
from clinical.experiment_history import append_record, record_from_report, read_history, summarize_history

class ExperimentHistoryTests(unittest.TestCase):
    def setUp(self):
        self.report = compare(synthetic_examples())
        self.record = record_from_report("run_001", "synthetic-model", self.report,
                                         recorded_at=datetime(2026, 11, 18, tzinfo=timezone.utc))

    def test_record_has_metadata_only(self):
        self.assertEqual(self.record.total, 6)
        self.assertFalse(hasattr(self.record, "prompt"))
        self.assertFalse(hasattr(self.record, "api_key"))

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "runs.jsonl"
            append_record(path, self.record)
            self.assertEqual(read_history(path)[0].run_id, "run_001")

    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "runs.jsonl"
            append_record(path, self.record)
            with self.assertRaises(ValueError):
                append_record(path, self.record)

    def test_invalid_model_identifier_rejected(self):
        with self.assertRaises(ValueError):
            record_from_report("run_001", "secret key with spaces", self.report)

    def test_summary(self):
        summary = summarize_history((self.record,))
        self.assertEqual(summary[0]["model"], "synthetic-model")

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "actual"
            source.write_text("")
            link = Path(folder) / "link"
            link.symlink_to(source)
            with self.assertRaises(ValueError):
                append_record(link, self.record)

if __name__ == "__main__":
    unittest.main()
