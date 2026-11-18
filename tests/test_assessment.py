import hashlib
import unittest
from datetime import date
from clinical.assessment import AssessmentPipeline, AssessmentStatus, Claim
from clinical.evidence_engine import EvidenceDocument, LocalEvidenceIndex
from clinical.models import ClinicalCase


def case(**changes):
    fields = dict(case_id="SYN-1", synthetic=True, hiv_rna_copies_ml=100,
                  cd4_cells_mm3=400, egfr_ml_min_173m2=80,
                  hbv_status="negative", resistance_history="none documented",
                  current_medications=("synthetic-medication",))
    fields.update(changes)
    return ClinicalCase(**fields)


def index():
    content = "Synthetic evidence about monitoring only."
    record = dict(document_id="SYN-DOC", title="Synthetic fixture",
                  url="https://clinicalinfo.hiv.gov/en/guidelines",
                  version="test", published_on="2026-10-01",
                  retrieved_at="2026-11-01T00:00:00Z", content=content,
                  sha256_digest=hashlib.sha256(content.encode()).hexdigest())
    return LocalEvidenceIndex([EvidenceDocument.from_record(record)])


class Generator:
    def __init__(self, claims):
        self.claims = claims

    def generate(self, case, evidence):
        return self.claims


class AssessmentTests(unittest.TestCase):
    def test_missing_case_context_abstains_before_retrieval(self):
        result = AssessmentPipeline(index()).assess(case(hbv_status="unknown"), "monitoring",
                                                    as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.ABSTAIN)
        self.assertEqual(result.evidence, ())

    def test_missing_evidence_abstains(self):
        result = AssessmentPipeline(index()).assess(case(), "unrelated", as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.ABSTAIN)

    def test_no_generator_abstains(self):
        result = AssessmentPipeline(index()).assess(case(), "monitoring", as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.ABSTAIN)

    def test_hallucinated_citation_abstains(self):
        generator = Generator((Claim("Synthetic claim", ("NONEXISTENT",)),))
        result = AssessmentPipeline(index(), generator).assess(case(), "monitoring",
                                                               as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.ABSTAIN)
        self.assertEqual(result.claims, ())

    def test_blank_claim_abstains(self):
        generator = Generator((Claim(" ", ("SYN-DOC",)),))
        result = AssessmentPipeline(index(), generator).assess(case(), "monitoring",
                                                               as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.ABSTAIN)

    def test_cited_claim_requires_review(self):
        generator = Generator((Claim("Synthetic claim for review", ("SYN-DOC",)),))
        result = AssessmentPipeline(index(), generator).assess(case(), "monitoring",
                                                               as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.EVIDENCE_REVIEW)
        self.assertIn("clinician", result.warnings[0])

    def test_stale_evidence_abstains(self):
        result = AssessmentPipeline(LocalEvidenceIndex(index().documents, max_age_days=1)).assess(
            case(), "monitoring", as_of=date(2026, 11, 17))
        self.assertEqual(result.status, AssessmentStatus.ABSTAIN)


if __name__ == "__main__":
    unittest.main()
