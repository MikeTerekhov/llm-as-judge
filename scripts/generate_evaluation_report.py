"""Generate a reproducible synthetic evaluation report locally, no model calls."""
import argparse
import json
from pathlib import Path

from clinical.benchmark_quality_gates import QualityThresholds
from clinical.human_adjudication import read_reviews
from clinical.reproducible_report import build_report, verify_report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews", default="local/reviews.jsonl")
    parser.add_argument("--output", default="local/evaluation-report.json")
    parser.add_argument("--experiment-id")
    parser.add_argument("--min-review-coverage", type=float, default=1.0)
    parser.add_argument("--min-double-review-coverage", type=float, default=1.0)
    parser.add_argument("--max-disputed-fraction", type=float, default=0.0)
    parser.add_argument("--min-pairwise-kappa", type=float, default=0.6)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    policy = QualityThresholds(args.min_review_coverage, args.min_double_review_coverage,
                               args.max_disputed_fraction, args.min_pairwise_kappa)
    report = build_report(read_reviews(args.reviews), policy, experiment_id=args.experiment_id)
    if not verify_report(report):
        raise RuntimeError("Report checksum verification failed")
    output = Path(args.output)
    if output.is_symlink():
        raise ValueError("Output must not be a symlink")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Report: {output} sha256={report['report_sha256']} quality={report['quality_gates']['status']}")
    if args.require_pass and report["quality_gates"]["status"] != "pass":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
