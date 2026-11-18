"""Local operator CLI for fictional benchmark review, no network or patient data."""
import argparse
import json
from clinical.human_adjudication import make_review, append_review, read_reviews, adjudication_report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="local/reviews.jsonl")
    parser.add_argument("--example", help="Synthetic example ID")
    parser.add_argument("--reviewer", help="Pseudonymous reviewer ID")
    parser.add_argument("--label", choices=["supported","contradicted","insufficient_evidence"])
    parser.add_argument("--note", default="")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.report:
        report = adjudication_report(read_reviews(args.history))
        print(json.dumps(report, indent=2))
        return
    if not all((args.example, args.reviewer, args.label)):
        parser.error("--example, --reviewer and --label are required unless --report")
    append_review(args.history, make_review(args.example, args.reviewer, args.label, args.note))
    print("Synthetic review recorded locally.")

if __name__ == "__main__":
    main()
