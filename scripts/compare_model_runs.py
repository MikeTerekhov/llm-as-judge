"""Compare two or more saved synthetic model benchmark reports offline."""
import argparse
import json
from pathlib import Path
from clinical.model_run_comparison import compare_runs

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline comparison of synthetic LLM benchmark runs")
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if len(args.reports) < 2:
        parser.error("At least two report files are required")
    if args.output and args.output.exists():
        parser.error("Refusing to overwrite existing comparison")
    try:
        runs = []
        for path in args.reports:
            if path.stat().st_size > 1024 * 1024:
                raise ValueError("Input report exceeds 1 MiB")
            runs.append(json.loads(path.read_text(encoding="utf-8")))
        result = compare_runs(runs)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
        print("Saved comparison to", args.output)
    else:
        print(serialized)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
