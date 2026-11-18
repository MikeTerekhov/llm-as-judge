"""Read-only local synthetic reviewer reliability metrics, disabled by default."""
import os
from fastapi import APIRouter, HTTPException
from clinical.human_adjudication import read_reviews
from clinical.reviewer_reliability import reliability_report

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/reliability")
def reliability():
    if os.environ.get("AI_REGIMEN_ENABLE_REVIEW_API") != "true":
        raise HTTPException(status_code=404, detail="Review metrics not enabled")
    path = os.environ.get("AI_REGIMEN_REVIEW_PATH", "")
    if not path:
        raise HTTPException(status_code=503, detail="Review path not configured")
    try:
        return reliability_report(read_reviews(path))
    except (OSError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=503, detail="Review metrics unavailable")
