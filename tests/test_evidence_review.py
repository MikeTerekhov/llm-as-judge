import hashlib
import unittest
from datetime import datetime, timezone
from clinical.evidence_engine import EvidenceDocument, EvidenceError
from clinical.evidence_review import ReviewRecord, approved_documents

def fixture():
    content = "Synthetic research evidence only."
    return EvidenceDocument.from_record({
        "document_id": "SYN-1", "title": "Synthetic", "url": "https://clinicalinfo.hiv.gov/en/guidelines",
        "version": "test", "published_on": "2026-10-01",
        "retrieved_at": "2026-11-01T00:00:00Z", "content": content,
        "sha256_digest": hashlib.sha256(content.encode()).hexdigest()
    })

def review(doc, **changes):
    data = dict(document_id=doc.document_id, sha256_digest=doc.sha256_digest,
                reviewer="synthetic-reviewer", reviewed_at="2026-11-02T00:00:00Z",
                source_checked=True, tables_checked=True, notes="Synthetic fixture only")
    data.update(changes)
    return ReviewRecord.from_record(data)

class ReviewTests(unittest.TestCase):
    def test_approved_snapshot(self):
        doc = fixture()
        self.assertEqual(approved_documents([doc], [review(doc)]), [doc])

    def test_missing_review_fails_closed(self):
        self.assertEqual(approved_documents([fixture()], []), [])

    def test_hash_mismatch_fails_closed(self):
        doc = fixture()
        self.assertEqual(approved_documents([doc], [review(doc, sha256_digest="0"*64)]), [])

    def test_unchecked_tables_fails_closed(self):
        doc = fixture()
        self.assertEqual(approved_documents([doc], [review(doc, tables_checked=False)]), [])

    def test_review_before_retrieval_fails_closed(self):
        doc = fixture()
        self.assertEqual(approved_documents([doc], [review(doc, reviewed_at="2026-10-01T00:00:00Z")]), [])

    def test_duplicate_review_rejected(self):
        doc = fixture()
        with self.assertRaises(EvidenceError):
            approved_documents([doc], [review(doc), review(doc)])

    def test_timezone_required(self):
        doc = fixture()
        with self.assertRaises(EvidenceError):
            review(doc, reviewed_at="2026-11-02T00:00:00")

if __name__ == "__main__":
    unittest.main()
