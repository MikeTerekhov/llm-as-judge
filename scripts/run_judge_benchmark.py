"""Run the synthetic benchmark fixture without API calls or model access."""
import json
from dataclasses import asdict
from tests.test_judge_benchmark import fixture
from clinical.judge_benchmark import evaluate

if __name__ == "__main__":
    print(json.dumps(asdict(evaluate(fixture())), indent=2, sort_keys=True))
