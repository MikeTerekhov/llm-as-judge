"""Offline comparison of signed-by-checksum (not cryptographically signed) reports."""
import argparse
import json
from pathlib import Path
from clinical.evaluation_regression import compare_reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--output", default="artifacts/evaluation-regression.json")
    parser.add_argument("--allow-fixture-changes", action="store_true")
    args = parser.parse_args()
    old = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    new = json.loads(Path(args.current).read_text(encoding="utf-8"))
    result = compare_reports(old, new, allow_fixture_changes=args.allow_fixture_changes)
    target = Path(args.output)
    if target.is_symlink():
        raise ValueError("Output must not be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"Evaluation regression: {result['status']}; blockers={result['blockers']}")
    if result["status"] != "pass":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
