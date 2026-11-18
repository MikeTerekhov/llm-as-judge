import unittest

from clinical.models import ClinicalCase
from clinical.validation import review_case
from clinical.evidence import EmptyEvidenceProvider


class ClinicalFoundationTests(unittest.TestCase):
    def test_rejects_real_patient_input(self):
        with self.assertRaises(ValueError):
            ClinicalCase(case_id="1", synthetic=False)

    def test_missing_information_causes_abstention(self):
        result = review_case(ClinicalCase(case_id="SYN-001", synthetic=True, cd4_cells_mm3=385))
        self.assertFalse(result.ready_for_evidence_review)
        self.assertIn("hbv_status", result.missing_fields)

    def test_complete_synthetic_case(self):
        case = ClinicalCase(
            case_id="SYN-002", synthetic=True, hiv_rna_copies_ml=42000,
            cd4_cells_mm3=385, egfr_ml_min_173m2=78,
            hbv_status="negative", resistance_history="none documented",
            current_medications=("synthetic-medication",),
        )
        self.assertTrue(review_case(case).ready_for_evidence_review)

    def test_invalid_lab_value(self):
        with self.assertRaises(ValueError):
            ClinicalCase(case_id="SYN-003", synthetic=True, cd4_cells_mm3=-1)

    def test_evidence_provider_does_not_invent_sources(self):
        self.assertEqual(EmptyEvidenceProvider().search("ART"), [])


if __name__ == "__main__":
    unittest.main()
