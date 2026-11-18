import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from api.evaluation_history import evaluation_history

class EvaluationHistoryApiTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                evaluation_history()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_empty_local_history(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "AI_REGIMEN_ENABLE_EVALUATION_HISTORY_API": "true",
                "AI_REGIMEN_EVALUATION_HISTORY_DIR": directory}, clear=True):
                result = evaluation_history()
            self.assertEqual(result["count"], 0)

if __name__ == "__main__":
    unittest.main()
