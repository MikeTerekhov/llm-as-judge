"""Deterministic offline synthetic evaluation artifact for GitHub Actions.

No reviewer records, credentials, clinical records or external models are used.
"""
import argparse
import json
from pathlib import Path
from clinical.reproducible_report import build_report, verify_report


def generate() -> dict:
    first = build_report((), experiment_id="ci-synthetic")
    second = build_report((), experiment_id="ci-synthetic")
    if not verify_report(first) or not verify_report(second):
        raise RuntimeError("Synthetic report integrity verification failed")
    if first != second:
        raise RuntimeError("Synthetic report is not deterministic")
    if first["quality_gates"]["status"] != "blocked":
        raise RuntimeError("Empty human-review dataset must fail closed")
    if first["review_count"] != 0:
        raise RuntimeError("CI report must not contain human reviews")
    return first


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/synthetic-evaluation.json")
    args = parser.parse_args()
    target = Path(args.output)
    if target.is_symlink():
        raise ValueError("Refusing to write to a symlink")
    report = generate()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    loaded = json.loads(target.read_text(encoding="utf-8"))
    if not verify_report(loaded) or loaded != report:
        raise RuntimeError("Written report failed round-trip integrity verification")
    print(f"Verified synthetic evaluation: {report['report_sha256']}")
    print("Human review quality: blocked (expected, no reviewers in CI)")


if __name__ == "__main__":
    main()
