"""Load reviewed local snapshots on demand; never fetch remotely from requests."""
import os
from pathlib import Path
from clinical.evidence_review import load_approved_index
from clinical.evidence_engine import LocalEvidenceIndex

def get_index() -> LocalEvidenceIndex:
    snapshot = os.environ.get("AI_REGIMEN_SNAPSHOT_PATH")
    reviews = os.environ.get("AI_REGIMEN_REVIEW_PATH")
    if not snapshot or not reviews:
        return LocalEvidenceIndex([])
    if not Path(snapshot).is_file() or not Path(reviews).is_file():
        raise RuntimeError("Configured evidence files are missing")
    return load_approved_index(snapshot, reviews)
