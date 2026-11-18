"""Read-only synthetic experiment analytics from an operator-selected local JSONL file.

Disabled unless explicitly configured. Never serves raw records or prompts.
"""
import os
from fastapi import APIRouter, HTTPException
from clinical.experiment_analytics import analytics
from clinical.experiment_history import read_history

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/experiments")
def experiments():
    if os.environ.get("AI_REGIMEN_ENABLE_HISTORY_API") != "true":
        raise HTTPException(status_code=404, detail="Experiment history not enabled")
    path = os.environ.get("AI_REGIMEN_HISTORY_PATH", "")
    if not path:
        raise HTTPException(status_code=503, detail="History path not configured")
    try:
        records = read_history(path)
        return analytics(records)
    except (OSError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=503, detail="Experiment history unavailable")
