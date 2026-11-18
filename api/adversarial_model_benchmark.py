"""Read-only offline model benchmark status; never invokes external providers."""
from fastapi import APIRouter
from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_model_benchmark import benchmark_adversarial

router = APIRouter(prefix="/api/v1/judge", tags=["synthetic-judge"])

@router.get("/adversarial-model")
def adversarial_model():
    return benchmark_adversarial(adversarial_examples())
