import hashlib
import io
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from email.message import Message
from clinical.ingestion import validate_url, fetch_guideline, build_snapshot, MAX_BYTES
from clinical.evidence_engine import EvidenceError, EvidenceDocument

URL = "https://clinicalinfo.hiv.gov/en/guidelines"

class FakeResponse:
    status = 200
    def __init__(self, data=b"<html><body><main><h1>Synthetic evidence</h1><p>Monitoring example</p></main></body></html>",
                 content_type="text/html; charset=utf-8"):
        self.data = data
        self.headers = Message()
        self.headers["Content-Type"] = content_type
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, count): return self.data[:count]

class FakeOpener:
    def __init__(self, response): self.response = response
    def open(self, request, timeout): return self.response

class IngestionTests(unittest.TestCase):
    def test_rejects_untrusted_url(self):
        for url in ["http://clinicalinfo.hiv.gov/a", "https://clinicalinfo.hiv.gov.evil.test/a",
                    "https://clinicalinfo.hiv.gov/a?redirect=x"]:
            with self.assertRaises(EvidenceError): validate_url(url)

    @patch("clinical.ingestion.build_opener")
    def test_extracts_html(self, opener):
        opener.return_value = FakeOpener(FakeResponse())
        self.assertIn("Monitoring example", fetch_guideline(URL))

    @patch("clinical.ingestion.build_opener")
    def test_rejects_non_html(self, opener):
        opener.return_value = FakeOpener(FakeResponse(content_type="application/pdf"))
        with self.assertRaises(EvidenceError): fetch_guideline(URL)

    @patch("clinical.ingestion.build_opener")
    def test_rejects_oversized(self, opener):
        opener.return_value = FakeOpener(FakeResponse(data=b"x" * (MAX_BYTES + 1)))
        with self.assertRaises(EvidenceError): fetch_guideline(URL)

    def test_snapshot_integrity(self):
        record = build_snapshot(document_id="SYN-1", title="Synthetic", url=URL,
                                version="test", published_on="2026-10-01",
                                content="Synthetic text", retrieved_at=datetime(2026, 11, 18, tzinfo=timezone.utc))
        self.assertEqual(EvidenceDocument.from_record(record).content, "Synthetic text")
        self.assertEqual(record["sha256_digest"], hashlib.sha256(b"Synthetic text").hexdigest())

if __name__ == "__main__":
    unittest.main()
