import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)
CASE = dict(case_id="SYN-007", synthetic=True, hiv_rna_copies_ml=100,
            cd4_cells_mm3=400, egfr_ml_min_173m2=80, hbv_status="negative",
            resistance_history="none documented", current_medications=["fictional-med"])

class EvidenceApiTests(unittest.TestCase):
    def test_unconfigured_is_empty(self):
        with patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/v1/evidence?query=monitoring")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["hits"], [])

    def test_approved_snapshot_visible_without_recommendations(self):
        with tempfile.TemporaryDirectory() as directory:
            content = "Synthetic monitoring research passage."
            digest = hashlib.sha256(content.encode()).hexdigest()
            snapshot = [dict(document_id="SYN-EVIDENCE", title="Synthetic fixture",
                             url="https://clinicalinfo.hiv.gov/en/guidelines", version="test",
                             published_on="2026-10-01", retrieved_at="2026-11-01T00:00:00Z",
                             content=content, sha256_digest=digest)]
            review = [dict(document_id="SYN-EVIDENCE", sha256_digest=digest,
                           reviewer="test-reviewer", reviewed_at="2026-11-02T00:00:00Z",
                           source_checked=True, tables_checked=True, notes="Synthetic fixture")]
            a, b = Path(directory)/"snapshot.json", Path(directory)/"review.json"
            a.write_text(json.dumps(snapshot)); b.write_text(json.dumps(review))
            with patch.dict("os.environ", {"AI_REGIMEN_SNAPSHOT_PATH":str(a),
                                            "AI_REGIMEN_REVIEW_PATH":str(b)}):
                response = client.get("/api/v1/evidence?query=monitoring")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["hits"][0]["document_id"], "SYN-EVIDENCE")
                result = client.post("/api/v1/cases/assess", json=CASE).json()
                self.assertEqual(result["status"], "abstain")
                self.assertEqual(result["claims"], [])
                self.assertEqual(result["evidence"][0]["document_id"], "SYN-EVIDENCE")

    def test_unreviewed_snapshot_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            content = "Synthetic monitoring."
            digest = hashlib.sha256(content.encode()).hexdigest()
            a,b = Path(directory)/"snapshot.json",Path(directory)/"review.json"
            a.write_text(json.dumps([dict(document_id="SYN-E",title="Fixture",
                url="https://clinicalinfo.hiv.gov/en/guidelines",version="test",
                published_on="2026-10-01",retrieved_at="2026-11-01T00:00:00Z",
                content=content,sha256_digest=digest)]))
            b.write_text("[]")
            with patch.dict("os.environ", {"AI_REGIMEN_SNAPSHOT_PATH":str(a),
                                            "AI_REGIMEN_REVIEW_PATH":str(b)}):
                self.assertEqual(client.get("/api/v1/evidence?query=monitoring").json()["hits"], [])

if __name__ == "__main__":
    unittest.main()
