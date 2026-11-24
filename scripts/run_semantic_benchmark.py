"""Operator-only NLI benchmark on the fictional adversarial set. Runs a local model.

Example:
    pip install -r requirements-nli.txt
    python -m scripts.run_semantic_benchmark --allow-download --revision <commit>
    python -m scripts.run_semantic_benchmark --dataset expanded --split dev --rows
"""
import argparse
import json

from clinical.adversarial_expanded import expanded_examples
from clinical.adversarial_fixtures import adversarial_examples
from clinical.nli_backends import DEFAULT_NLI_MODEL, make_transformers_nli
from clinical.semantic_benchmark import benchmark_semantic

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=DEFAULT_NLI_MODEL)
    parser.add_argument("--revision", help="Model commit hash; pin for reproducibility")
    parser.add_argument("--allow-download", action="store_true",
                        help="Fetch the model if not already cached locally")
    parser.add_argument("--dataset", choices=("core", "expanded"), default="core",
                        help="core: the 12 hand-authored examples; expanded: 360 generated ones")
    parser.add_argument("--split", choices=("all", "dev", "test"), default="all",
                        help="expanded dataset only; tune on dev, report test")
    parser.add_argument("--rows", action="store_true", help="include per-example rows")
    parser.add_argument("--support-threshold", type=float, default=0.9)
    parser.add_argument("--contradiction-threshold", type=float, default=0.9)
    args = parser.parse_args(argv)
    if args.dataset == "core" and args.split != "all":
        parser.error("--split applies to the expanded dataset only")
    examples = adversarial_examples() if args.dataset == "core" else expanded_examples(args.split)
    scorer = make_transformers_nli(args.model, revision=args.revision,
                                   local_files_only=not args.allow_download)
    name = f"{args.model}@{args.revision or 'unpinned'}"
    report = benchmark_semantic(examples, scorer, scorer_name=name,
                                support_threshold=args.support_threshold,
                                contradiction_threshold=args.contradiction_threshold)
    report["dataset"], report["split"] = args.dataset, args.split
    if not args.rows:
        report.pop("rows")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
