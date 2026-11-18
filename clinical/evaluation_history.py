"""Verified, bounded history of synthetic evaluation report snapshots."""
from pathlib import Path
import json
import re
from .reproducible_report import verify_report
from .evaluation_regression import compare_reports

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_REPORTS = 100
MAX_BYTES = 2_000_000

def load_history(directory: str | Path) -> dict:
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("History directory unavailable")
    files = sorted(root.glob("*.json"))
    if len(files) > MAX_REPORTS:
        raise ValueError("Too many history reports")
    entries = []
    previous = None
    for path in files:
        if path.is_symlink() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid report file")
        report = json.loads(path.read_text(encoding="utf-8"))
        if not verify_report(report):
            raise ValueError("Unverified report")
        regression = compare_reports(previous, report) if previous else None
        entries.append({
            "snapshot": path.stem,
            "report_sha256": report["report_sha256"],
            "dataset_sha256": report["dataset_sha256"],
            "fixture_count": report["fixture_count"],
            "review_count": report["review_count"],
            "quality_status": report["quality_gates"]["status"],
            "regression_status": regression["status"] if regression else None,
            "regression_blockers": regression["blockers"] if regression else [],
            "changed_examples": len(regression["changed_examples"]) if regression else 0,
            "review_counts_changed": regression["review_counts_changed"] if regression else False,
        })
        previous = report
    return {"snapshots": entries, "count": len(entries),
            "disclaimer": "Verified synthetic reports only. Consistency is not clinical accuracy."}

def save_snapshot(directory: str | Path, snapshot: str, report: dict) -> Path:
    if not SAFE_ID.fullmatch(snapshot) or not verify_report(report):
        raise ValueError("Invalid snapshot name or report checksum")
    root = Path(directory)
    if root.is_symlink():
        raise ValueError("History directory cannot be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    path = root / (snapshot + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return path
