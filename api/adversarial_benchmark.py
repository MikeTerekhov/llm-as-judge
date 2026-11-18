"""Static adversarial dataset diagnostics; no model calls."""
from fastapi import APIRouter
from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_evaluation import evaluate_adversarial

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/adversarial")
def adversarial():
    return evaluate_adversarial(adversarial_examples())
