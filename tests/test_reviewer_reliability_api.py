import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from api.reviewer_reliability import reliability
from clinical.human_adjudication import append_review, make_review

class ReliabilityApiTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                reliability()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_local_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "reviews.jsonl"
            append_review(path, make_review("negation-reversal","r1","contradicted"))
            append_review(path, make_review("negation-reversal","r2","supported"))
            with patch.dict(os.environ, {"AI_REGIMEN_ENABLE_REVIEW_API": "true",
                                         "AI_REGIMEN_REVIEW_PATH": str(path)}, clear=True):
                result = reliability()
            self.assertEqual(result["categories"]["negation"]["disputed"], 1)
            self.assertNotIn("note", str(result))

if __name__ == "__main__":
    unittest.main()
