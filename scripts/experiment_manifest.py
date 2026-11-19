"""Generate and verify a reproducibility manifest for an executed synthetic benchmark."""
import argparse
import json
from pathlib import Path

from clinical.experiment_manifest import build_manifest, verify_manifest

MAX_INPUT = 1024 * 1024

def _read(path: Path):
    if path.stat().st_size > MAX_INPUT:
        raise ValueError("Input exceeds 1 MiB")
    return json.loads(path.read_text(encoding="utf-8"))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Synthetic benchmark experiment manifests")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("report", type=Path)
    create.add_argument("--experiment-id", required=True)
    create.add_argument("--model-version", required=True)
    create.add_argument("--dataset-version", default="synthetic-adversarial-v1")
    create.add_argument("--prompt-version", default="llm-judge-v1")
    create.add_argument("--notes", default="")
    create.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            if args.output.exists():
                raise ValueError("Refusing to overwrite existing manifest")
            result = build_manifest(_read(args.report), experiment_id=args.experiment_id,
                                    model_version=args.model_version,
                                    dataset_version=args.dataset_version,
                                    prompt_version=args.prompt_version, notes=args.notes)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
            print("Manifest saved to", args.output)
        else:
            verify_manifest(_read(args.manifest), _read(args.report))
            print("Manifest matches report checksum and declared model.")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
