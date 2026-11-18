"""Explicitly opted-in operator CLI; emits no prompts, excerpts, or credentials."""
import json
from dataclasses import asdict
from clinical.secure_model_runner import load_config, run_synthetic_comparison

def main():
    config = load_config()
    report = run_synthetic_comparison(config)
    print(json.dumps({
        "total": report.total,
        "model_attempted": report.model_attempted,
        "model_returned": report.model_returned,
        "disagreement_count": report.disagreement_count,
        "disagreement_rate": report.disagreement_rate,
        "outcomes": [{"example_id": row.example_id, "disposition": row.disposition,
                      "model_verdict": row.model_verdict, "disagreement": row.disagreement}
                     for row in report.rows],
    }, indent=2))

if __name__ == "__main__":
    main()
