import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from clinical.benchmark_fixtures import synthetic_examples
from clinical.model_comparison import compare
from clinical.experiment_history import append_record, record_from_report
from clinical.experiment_analytics import analytics
from api.experiment_analytics import experiments

class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        report = compare(synthetic_examples())
        self.one = record_from_report("run_1", "model-a", report,
                                      recorded_at=datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.two = record_from_report("run_2", "model-b", report,
                                      recorded_at=datetime(2026, 11, 2, tzinfo=timezone.utc))

    def test_empty(self):
        self.assertEqual(analytics(())["runs"], 0)

    def test_model_grouping(self):
        result = analytics((self.two, self.one))
        self.assertEqual(result["runs"], 2)
        self.assertEqual([x["model"] for x in result["models"]], ["model-a", "model-b"])
        self.assertEqual(result["trends"][0]["run_id"], "run_1")

    def test_no_judgments_has_null_rate(self):
        result = analytics((self.one,))
        self.assertIsNone(result["models"][0]["weighted_disagreement_rate"])

    def test_endpoint_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                experiments()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_enabled_endpoint_returns_aggregate_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "runs.jsonl"
            append_record(path, self.one)
            with patch.dict(os.environ, {"AI_REGIMEN_ENABLE_HISTORY_API": "true",
                                         "AI_REGIMEN_HISTORY_PATH": str(path)}, clear=True):
                result = experiments()
            self.assertEqual(result["runs"], 1)
            self.assertNotIn("outcomes", result["trends"][0])

if __name__ == "__main__":
    unittest.main()
