"""Opt-in read-only research audit metadata endpoint."""
import os
from fastapi import APIRouter, HTTPException
from clinical.research_audit import audit_summary

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/audit-trail")
def research_audit(release_id: str | None = None):
    if os.environ.get("AI_REGIMEN_ENABLE_AUDIT_API") != "true":
        raise HTTPException(status_code=404, detail="Research audit disabled")
    path = os.environ.get("AI_REGIMEN_AUDIT_PATH", "")
    if not path:
        raise HTTPException(status_code=503, detail="Audit path not configured")
    try:
        return audit_summary(path, release_id=release_id)
    except ValueError as exc:
        if "filter" in str(exc):
            raise HTTPException(status_code=422, detail="Invalid release filter")
        raise HTTPException(status_code=503, detail="Audit unavailable")
    except (OSError, TypeError, KeyError):
        raise HTTPException(status_code=503, detail="Audit unavailable")
