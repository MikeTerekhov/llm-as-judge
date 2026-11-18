"""FastAPI research endpoint. Synthetic cases only, no model calls."""
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from clinical.models import ClinicalCase
from clinical.validation import review_case
from clinical.assessment import AssessmentPipeline
from .evidence_store import get_index
from .judge_dashboard import router as judge_router
from .judge_comparison import router as comparison_router
from .experiment_analytics import router as experiment_router
from .adversarial_benchmark import router as adversarial_router
from .adversarial_model_benchmark import router as adversarial_model_router
from .human_adjudication import router as adjudication_router
from .reviewer_reliability import router as reliability_router
from .benchmark_quality_gates import router as quality_router
from clinical.evidence_engine import EvidenceError

app = FastAPI(title="AI Regimen Research API", version="0.7.0",
              description="Synthetic-case prototype. Not for clinical use.")
app.include_router(judge_router)
app.include_router(comparison_router)
app.include_router(experiment_router)
app.include_router(adversarial_router)
app.include_router(adversarial_model_router)
app.include_router(adjudication_router)
app.include_router(reliability_router)
app.include_router(quality_router)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

class CaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=200)
    case_id: str = Field(min_length=1, max_length=80, pattern=r"^SYN-[A-Za-z0-9_-]+$")
    synthetic: bool
    hiv_rna_copies_ml: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    cd4_cells_mm3: int | None = Field(default=None, ge=0)
    egfr_ml_min_173m2: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    hbv_status: str | None = None
    resistance_history: str | None = Field(default=None, max_length=200)
    current_medications: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("synthetic")
    @classmethod
    def require_synthetic(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Only explicitly synthetic cases are accepted")
        return value

    @field_validator("hbv_status")
    @classmethod
    def validate_hbv(cls, value: str | None) -> str | None:
        if value not in (None, "positive", "negative", "unknown"):
            raise ValueError("Invalid HBV status")
        return value

    @field_validator("current_medications")
    @classmethod
    def validate_medications(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 80 for item in value):
            raise ValueError("Invalid medication entry")
        return value

@app.get("/health")
def health():
    return {"status": "ok", "mode": "synthetic-research"}

@app.post("/api/v1/cases/review")
def case_review(payload: CaseInput):
    try:
        case = ClinicalCase(**{**payload.model_dump(), "current_medications": tuple(payload.current_medications)})
        review = review_case(case)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return asdict(review)

@app.post("/api/v1/cases/assess")
def assess_case(payload: CaseInput):
    try:
        case = ClinicalCase(**{**payload.model_dump(), "current_medications": tuple(payload.current_medications)})
        assessment = AssessmentPipeline(get_index()).assess(case, "monitoring")
    except (OSError, ValueError, RuntimeError, EvidenceError) as exc:
        raise HTTPException(status_code=503, detail="Evidence configuration unavailable") from exc
    return asdict(assessment)

@app.get("/api/v1/evidence")
def evidence_search(query: str = ""):
    if not query.strip() or len(query) > 120:
        raise HTTPException(status_code=422, detail="Query must be 1-120 characters")
    try:
        hits = get_index().search(query)
    except (OSError, ValueError, RuntimeError, EvidenceError) as exc:
        raise HTTPException(status_code=503, detail="Evidence configuration unavailable") from exc
    return {"hits": [asdict(hit) for hit in hits],
            "disclaimer": "Operator-reviewed research snapshots only; not clinically validated."}

