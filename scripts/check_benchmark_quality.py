"""Operator quality gate CLI. Exit 1 when review quality is insufficient."""
import argparse
import json
from clinical.benchmark_quality_gates import QualityThresholds, assess_quality
from clinical.human_adjudication import read_reviews

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="local/reviews.jsonl")
    parser.add_argument("--min-review-coverage", type=float, default=1.0)
    parser.add_argument("--min-double-review-coverage", type=float, default=1.0)
    parser.add_argument("--max-disputed-fraction", type=float, default=0.0)
    parser.add_argument("--min-pairwise-kappa", type=float, default=0.6)
    args = parser.parse_args()
    policy = QualityThresholds(args.min_review_coverage,
                               args.min_double_review_coverage,
                               args.max_disputed_fraction,
                               args.min_pairwise_kappa)
    report = assess_quality(read_reviews(args.history), policy)
    print(json.dumps(report, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
