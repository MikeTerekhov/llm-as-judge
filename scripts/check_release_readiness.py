"""Local, read-only release-readiness CLI. Never promotes or deploys."""
import argparse
import json
from pathlib import Path
from clinical.release_readiness import assess_release

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--regression", help="Optional regression JSON")
    parser.add_argument("--allow-missing-regression", action="store_true",
                        help="For local diagnostics only; do not use for release approval")
    parser.add_argument("--output", default="artifacts/release-readiness.json")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    regression = (json.loads(Path(args.regression).read_text(encoding="utf-8"))
                  if args.regression else None)
    result = assess_release(report, regression,
                            regression_required=not args.allow_missing_regression)
    target = Path(args.output)
    if target.is_symlink():
        raise ValueError("Output must not be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Release readiness: {result['status']} ({', '.join(result['blockers']) or 'no blockers'})")
    if result["status"] != "ready_for_manual_research_review":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
