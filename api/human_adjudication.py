"""Read-only local synthetic review summary, disabled by default."""
import os
from fastapi import APIRouter, HTTPException
from clinical.human_adjudication import adjudication_report, read_reviews

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/adjudication")
def adjudication():
    if os.environ.get("AI_REGIMEN_ENABLE_REVIEW_API") != "true":
        raise HTTPException(status_code=404, detail="Review summary not enabled")
    path = os.environ.get("AI_REGIMEN_REVIEW_PATH", "")
    if not path:
        raise HTTPException(status_code=503, detail="Review path not configured")
    try:
        return adjudication_report(read_reviews(path))
    except (OSError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=503, detail="Review summary unavailable")
