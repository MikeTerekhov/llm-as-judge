"""Assert synthetic CI artifacts remain blocked for research promotion."""
import json
from pathlib import Path
from clinical.evaluation_regression import compare_reports
from clinical.release_readiness import assess_release
from clinical.reproducible_report import verify_report

def main():
    path = Path("artifacts/synthetic-evaluation.json")
    report = json.loads(path.read_text(encoding="utf-8"))
    if not verify_report(report):
        raise RuntimeError("CI report checksum failed")
    regression = compare_reports(report, report)
    readiness = assess_release(report, regression)
    if readiness["status"] != "blocked" or "human_review_quality_blocked" not in readiness["blockers"]:
        raise RuntimeError("CI synthetic report unexpectedly ready for research review")
    target = Path("artifacts/release-readiness.json")
    target.write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Verified fail-closed research readiness: human review required")

if __name__ == "__main__":
    main()
