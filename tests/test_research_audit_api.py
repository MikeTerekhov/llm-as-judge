import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from api.research_audit import research_audit
from clinical.research_audit import append_audit

class AuditApiTests(unittest.TestCase):
    def test_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                research_audit()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_read_only_local_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"audit.jsonl"
            append_audit(path, event_type="manifest_registered",
                         release_id="research1", artifact_sha256="a"*64)
            with patch.dict(os.environ, {
                "AI_REGIMEN_ENABLE_AUDIT_API": "true",
                "AI_REGIMEN_AUDIT_PATH": str(path)}, clear=True):
                result = research_audit()
            self.assertEqual(result["total_events"], 1)

    def test_invalid_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "AI_REGIMEN_ENABLE_AUDIT_API": "true",
                "AI_REGIMEN_AUDIT_PATH": str(Path(directory)/"audit.jsonl")}, clear=True):
                with self.assertRaises(HTTPException) as ctx:
                    research_audit(release_id="../bad")
            self.assertEqual(ctx.exception.status_code, 422)

if __name__ == "__main__":
    unittest.main()
