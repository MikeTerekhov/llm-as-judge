"""Produce a pending, blocked manifest for the synthetic CI evaluation."""
import json
import os
from pathlib import Path
from clinical.evaluation_regression import compare_reports
from clinical.release_manifest import build_manifest, verify_manifest
from clinical.reproducible_report import verify_report

def main():
    report = json.loads(Path("artifacts/synthetic-evaluation.json").read_text(encoding="utf-8"))
    if not verify_report(report):
        raise RuntimeError("Invalid CI evaluation report")
    sha = os.environ.get("GITHUB_SHA", "")
    regression = compare_reports(report, report)
    manifest = build_manifest(report, regression, commit_sha=sha, approval="pending")
    if not verify_manifest(manifest) or manifest["readiness_status"] != "blocked":
        raise RuntimeError("CI manifest must be verified and blocked")
    target = Path("artifacts/research-release-manifest.json")
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Verified pending synthetic research manifest")

if __name__ == "__main__":
    main()
