"""Save and inspect local fictional model evaluation history."""
import argparse
import json
from pathlib import Path

from clinical.experiment_history_store import append_run, history_summary, read_history

def main(argv=None):
    parser = argparse.ArgumentParser(description="Local-only synthetic model evaluation history")
    parser.add_argument("--history", type=Path, default=Path("local/model-evaluation-history.json"))
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="Save one executed AR-039 JSON report")
    add.add_argument("report", type=Path)
    sub.add_parser("list", help="Show stored run dates, models and conditional agreement")
    args = parser.parse_args(argv)
    try:
        if args.command == "add":
            if args.report.stat().st_size > 1024 * 1024:
                raise ValueError("Input report exceeds 1 MiB")
            run = json.loads(args.report.read_text(encoding="utf-8"))
            output = append_run(args.history, run)
        else:
            output = {"runs": history_summary(read_history(args.history)),
                      "disclaimer": "Fictional authored-label agreement, not clinical accuracy."}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
