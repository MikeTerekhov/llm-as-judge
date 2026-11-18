import unittest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)
CASE = {
    "case_id": "SYN-001", "synthetic": True,
    "hiv_rna_copies_ml": 42000, "cd4_cells_mm3": 385,
    "egfr_ml_min_173m2": 78, "hbv_status": "unknown",
    "resistance_history": None, "current_medications": []
}

class ApiTests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(client.get("/health").json()["mode"], "synthetic-research")

    def test_missing_fields(self):
        response = client.post("/api/v1/cases/review", json=CASE)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["ready_for_evidence_review"])
        self.assertIn("resistance_history", response.json()["missing_fields"])

    def test_no_real_cases(self):
        response = client.post("/api/v1/cases/review", json={**CASE, "synthetic": False})
        self.assertEqual(response.status_code, 422)

    def test_case_id_must_be_synthetic(self):
        response = client.post("/api/v1/cases/review", json={**CASE, "case_id": "PATIENT-123"})
        self.assertEqual(response.status_code, 422)

    def test_no_regimen_generated(self):
        response = client.post("/api/v1/cases/assess", json={**CASE,
            "hbv_status": "negative", "resistance_history": "none",
            "current_medications": ["synthetic-medication"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "abstain")
        self.assertEqual(response.json()["claims"], [])

    def test_unknown_fields_rejected(self):
        response = client.post("/api/v1/cases/review", json={**CASE, "patient_name": "Do Not Store"})
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
