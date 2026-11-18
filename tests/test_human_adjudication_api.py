import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from api.human_adjudication import adjudication
from clinical.human_adjudication import append_review, make_review

class AdjudicationApiTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                adjudication()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_local_read_only_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "reviews.jsonl"
            append_review(path, make_review("negation-reversal", "r1", "contradicted"))
            with patch.dict(os.environ, {"AI_REGIMEN_ENABLE_REVIEW_API": "true",
                                         "AI_REGIMEN_REVIEW_PATH": str(path)}, clear=True):
                result = adjudication()
            self.assertEqual(result["reviewed_examples"], 1)
            self.assertNotIn("note", result["rows"][0])

if __name__ == "__main__":
    unittest.main()
