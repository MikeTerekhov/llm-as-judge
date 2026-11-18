"""Opt-in synthetic model experiment with metadata-only local history."""
import argparse
import json
from dataclasses import asdict
from uuid import uuid4

from clinical.experiment_history import append_record, record_from_report, summarize_history, read_history
from clinical.secure_model_runner import load_config, run_synthetic_comparison

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="local/experiments.jsonl")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    config = load_config()
    report = run_synthetic_comparison(config)
    record = record_from_report(args.run_id or uuid4().hex, config.model, report)
    append_record(args.history, record)
    print(json.dumps(asdict(record), indent=2))

if __name__ == "__main__":
    main()
