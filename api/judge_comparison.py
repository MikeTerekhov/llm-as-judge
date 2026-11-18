"""No-network synthetic comparison endpoint.

An explicit model transport can be added later after privacy/security review.
"""
from dataclasses import asdict
from fastapi import APIRouter
from clinical.benchmark_fixtures import synthetic_examples
from clinical.model_comparison import compare

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/comparison")
def comparison():
    report = compare(synthetic_examples())
    return {**asdict(report), "model_enabled": False,
            "disclaimer": "No model configured or invoked. Disagreement rate is unavailable, not zero."}
