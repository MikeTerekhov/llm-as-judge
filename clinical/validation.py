"""Completeness checks, not clinical treatment rules."""
from dataclasses import dataclass
from .models import ClinicalCase


@dataclass(frozen=True)
class CaseReview:
    case_id: str
    ready_for_evidence_review: bool
    missing_fields: tuple[str, ...]
    warnings: tuple[str, ...]
    disclaimer: str = "Research prototype using synthetic data only. Not medical advice or a treatment recommendation."


def review_case(case: ClinicalCase) -> CaseReview:
    required = (
        "hiv_rna_copies_ml",
        "cd4_cells_mm3",
        "egfr_ml_min_173m2",
        "hbv_status",
        "resistance_history",
    )
    missing = tuple(name for name in required if getattr(case, name) is None or getattr(case, name) == "unknown" or getattr(case, name) == "")
    warnings = []
    if not case.current_medications:
        warnings.append("Medication list not provided; drug interaction assessment unavailable.")
    if missing:
        warnings.append("Missing clinical context; abstain from regimen selection.")
    return CaseReview(case.case_id, not missing and bool(case.current_medications), missing, tuple(warnings))
