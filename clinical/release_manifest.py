"""Integrity-checked research release manifest, not an authorization token."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from .reproducible_report import verify_report
from .release_readiness import assess_release

COMMIT = re.compile(r"^[a-f0-9]{40}$")
REVIEWER = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

def _digest(value: dict) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()

def build_manifest(report: dict, regression: dict | None, *, commit_sha: str,
                   reviewer_id: str | None = None, approval: str = "pending",
                   recorded_at: str | None = None) -> dict:
    if not COMMIT.fullmatch(commit_sha):
        raise ValueError("Expected full lowercase Git commit SHA")
    if approval not in ("pending", "approved", "rejected"):
        raise ValueError("Invalid approval status")
    if reviewer_id is not None and not REVIEWER.fullmatch(reviewer_id):
        raise ValueError("Invalid reviewer identifier")
    if approval != "pending" and reviewer_id is None:
        raise ValueError("Decision requires a reviewer identifier")
    if not verify_report(report):
        raise ValueError("Invalid report integrity")
    readiness = assess_release(report, regression)
    if approval == "approved" and readiness["status"] != "ready_for_manual_research_review":
        raise ValueError("Cannot approve blocked research report")
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must be timezone aware")
    manifest = {
        "schema_version": "1.0",
        "commit_sha": commit_sha,
        "recorded_at": timestamp,
        "report_sha256": report["report_sha256"],
        "dataset_sha256": report["dataset_sha256"],
        "review_counts_sha256": report["review_label_counts_sha256"],
        "quality_status": report["quality_gates"]["status"],
        "readiness_status": readiness["status"],
        "readiness_blockers": readiness["blockers"],
        "regression_baseline_sha256": regression.get("baseline_sha256") if regression else None,
        "regression_status": regression.get("status") if regression else None,
        "manual_review": {"reviewer_id": reviewer_id, "decision": approval},
        "disclaimer": "Research record only. Not proof of identity, clinical validation or deployment authorization.",
    }
    manifest["manifest_sha256"] = _digest(manifest)
    return manifest

def verify_manifest(manifest: dict) -> bool:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "1.0":
        return False
    digest = manifest.get("manifest_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    return _digest({k: v for k, v in manifest.items() if k != "manifest_sha256"}) == digest
