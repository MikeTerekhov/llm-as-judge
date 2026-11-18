"""Opt-in read-only quality gate summary from local fictional reviews."""
import os
from fastapi import APIRouter, HTTPException
from clinical.benchmark_quality_gates import assess_quality
from clinical.human_adjudication import read_reviews

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/quality-gates")
def quality_gates():
    if os.environ.get("AI_REGIMEN_ENABLE_REVIEW_API") != "true":
        raise HTTPException(status_code=404, detail="Review metrics not enabled")
    path = os.environ.get("AI_REGIMEN_REVIEW_PATH", "")
    if not path:
        raise HTTPException(status_code=503, detail="Review path not configured")
    try:
        return assess_quality(read_reviews(path))
    except (OSError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=503, detail="Quality gate data unavailable")
