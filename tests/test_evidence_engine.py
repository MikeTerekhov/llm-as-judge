import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from clinical.evidence_engine import EvidenceDocument, EvidenceError, LocalEvidenceIndex

def record(**overrides):
    content = overrides.pop("content", "Synthetic monitoring example.\n\nSynthetic resistance history example.")
    data = dict(document_id="SYN-1", title="Synthetic fixture",
                url="https://clinicalinfo.hiv.gov/en/guidelines", version="test-only",
                published_on="2026-10-01", retrieved_at="2026-11-01T12:00:00Z",
                content=content, sha256_digest=hashlib.sha256(content.encode()).hexdigest())
    data.update(overrides)
    return data

class EvidenceEngineTests(unittest.TestCase):
    def test_retrieval_provenance(self):
        idx = LocalEvidenceIndex([EvidenceDocument.from_record(record())])
        hits = idx.search("resistance history", as_of=date(2026, 11, 17))
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].version, "test-only")
        self.assertIn("resistance history", hits[0].excerpt)

    def test_no_match_abstains(self):
        idx = LocalEvidenceIndex([EvidenceDocument.from_record(record())])
        self.assertEqual(idx.search("unrelated", as_of=date(2026, 11, 17)), [])

    def test_stale_abstains(self):
        idx = LocalEvidenceIndex([EvidenceDocument.from_record(record())], max_age_days=5)
        self.assertEqual(idx.search("resistance", as_of=date(2026, 11, 17)), [])

    def test_tampered_content_rejected(self):
        with self.assertRaises(EvidenceError):
            EvidenceDocument.from_record(record(sha256_digest="0" * 64))

    def test_spoofed_domain_rejected(self):
        with self.assertRaises(EvidenceError):
            EvidenceDocument.from_record(record(url="https://clinicalinfo.hiv.gov.evil.example/path"))

    def test_missing_timezone_rejected(self):
        with self.assertRaises(EvidenceError):
            EvidenceDocument.from_record(record(retrieved_at="2026-11-01T12:00:00"))

    def test_duplicate_ids_rejected(self):
        doc = EvidenceDocument.from_record(record())
        with self.assertRaises(EvidenceError):
            LocalEvidenceIndex([doc, doc])

    def test_json_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            path.write_text(json.dumps([record()]), encoding="utf-8")
            self.assertEqual(len(LocalEvidenceIndex.from_json(str(path)).documents), 1)

if __name__ == "__main__":
    unittest.main()
