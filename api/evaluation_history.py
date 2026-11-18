"""Opt-in read-only synthetic evaluation history, never runs a model."""
import os
from fastapi import APIRouter, HTTPException
from clinical.evaluation_history import load_history

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/evaluation-history")
def evaluation_history():
    if os.environ.get("AI_REGIMEN_ENABLE_EVALUATION_HISTORY_API") != "true":
        raise HTTPException(status_code=404, detail="Evaluation history disabled")
    path = os.environ.get("AI_REGIMEN_EVALUATION_HISTORY_DIR", "")
    if not path:
        raise HTTPException(status_code=503, detail="Evaluation history not configured")
    try:
        return load_history(path)
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=503, detail="Evaluation history unavailable")
