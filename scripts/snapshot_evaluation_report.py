"""Save an immutable local synthetic evaluation report snapshot."""
import argparse
import json
from pathlib import Path
from clinical.evaluation_history import save_snapshot

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--snapshot", required=True, help="Sortable name such as 20261118_commitsha")
    parser.add_argument("--directory", default="local/evaluation-history")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    print(save_snapshot(args.directory, args.snapshot, report))

if __name__ == "__main__":
    main()
