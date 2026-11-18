"""Static, read-only synthetic benchmark. No model calls, user text or PHI."""
from dataclasses import asdict
from fastapi import APIRouter
from clinical.benchmark_fixtures import synthetic_examples
from clinical.claim_judge import judge_claim
from clinical.judge_benchmark import evaluate

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/benchmark")
def benchmark():
    examples = synthetic_examples()
    summary = asdict(evaluate(examples))
    rows = []
    for example in examples:
        judgment = judge_claim(example.claim, example.evidence)
        rows.append({
            "id": example.example_id,
            "category": example.category,
            "claim": example.claim.text,
            "expected": example.expected.value,
            "predicted": judgment.status.value,
            "lexical_coverage": judgment.lexical_coverage,
            "missing_terms": list(judgment.missing_terms),
            "reasons": list(judgment.reasons),
        })
    return {
        "summary": summary,
        "examples": rows,
        "model_enabled": False,
        "disclaimer": "Synthetic fixture only. Expected labels encode screener behavior, not clinical truth. No LLM is called.",
    }
