"""Explicit opt-in, bounded CLI runner for fictional adversarial benchmark.

No API route and no network calls unless the operator passes --execute.
"""
import argparse
import json
import os
from pathlib import Path

from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_model_benchmark import benchmark_adversarial
from clinical.openai_compatible_judge import make_chat_transport

def run(*, execute: bool, endpoint: str | None = None, model: str | None = None,
        api_key: str | None = None, timeout: int = 15) -> dict:
    examples = adversarial_examples()
    if not execute:
        return {"mode": "dry_run", "network_calls": 0,
                "fixture_count": len(examples),
                "report": benchmark_adversarial(examples),
                "disclaimer": "Dry run only; no external LLM called."}
    if not endpoint or not model or not api_key:
        raise ValueError("Explicit endpoint, model and API key are required for execution")
    transport = make_chat_transport(endpoint=endpoint, model=model, api_key=api_key,
                                    timeout=timeout)
    report = benchmark_adversarial(examples, transport)
    return {"mode": "executed", "fixture_count": len(examples),
            "model": model, "report": report,
            "disclaimer": "Fictional hand-authored labels; model agreement is not clinical accuracy."}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic-only opt-in LLM judge benchmark")
    parser.add_argument("--execute", action="store_true", help="Allow external model calls")
    parser.add_argument("--endpoint", default=None, help="Explicit HTTPS chat completions URL")
    parser.add_argument("--model", default=None, help="Explicit model identifier")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--output", type=Path, default=None,
                        help="Optional local JSON report; do not commit research results with secrets")
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        parser.error("Output already exists; refusing to overwrite")
    try:
        result = run(execute=args.execute, endpoint=args.endpoint, model=args.model,
                     api_key=os.environ.get("AI_REGIMEN_MODEL_API_KEY"), timeout=args.timeout)
    except ValueError as exc:
        parser.error(str(exc))
    serialized = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print("Saved synthetic benchmark report to", args.output)
    else:
        print(serialized)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
