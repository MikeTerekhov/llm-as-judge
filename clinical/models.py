"""Typed clinical case inputs. No treatment recommendations are generated."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ClinicalCase:
    case_id: str
    synthetic: bool
    hiv_rna_copies_ml: Optional[float] = None
    cd4_cells_mm3: Optional[int] = None
    egfr_ml_min_173m2: Optional[float] = None
    hbv_status: Optional[str] = None
    resistance_history: Optional[str] = None
    current_medications: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not self.case_id.strip():
            raise ValueError("case_id must not be blank")
        if not self.synthetic:
            raise ValueError("AR-001 accepts synthetic cases only; do not submit patient data")
        for name in ("hiv_rna_copies_ml", "cd4_cells_mm3", "egfr_ml_min_173m2"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value < float("inf")):
                raise ValueError(f"{name} must be a finite nonnegative number")
        if self.hbv_status is not None and self.hbv_status not in {"positive", "negative", "unknown"}:
            raise ValueError("hbv_status must be positive, negative, or unknown")
