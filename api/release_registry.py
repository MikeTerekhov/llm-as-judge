"""Disabled-by-default local research release registry metadata endpoint."""
import os
from fastapi import APIRouter, HTTPException
from clinical.release_registry import list_manifests

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/release-registry")
def release_registry(decision: str | None = None, commit_sha: str | None = None):
    if os.environ.get("AI_REGIMEN_ENABLE_RELEASE_REGISTRY_API") != "true":
        raise HTTPException(status_code=404, detail="Release registry disabled")
    directory = os.environ.get("AI_REGIMEN_RELEASE_REGISTRY_DIR", "")
    if not directory:
        raise HTTPException(status_code=503, detail="Registry path not configured")
    try:
        return list_manifests(directory, decision=decision, commit_sha=commit_sha)
    except ValueError as exc:
        if "filter" in str(exc):
            raise HTTPException(status_code=422, detail="Invalid registry filter")
        raise HTTPException(status_code=503, detail="Registry unavailable")
    except (OSError, KeyError, TypeError):
        raise HTTPException(status_code=503, detail="Registry unavailable")
