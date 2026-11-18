"""Operator-only adversarial benchmark. Emits synthetic IDs and aggregate metadata."""
import json
from clinical.adversarial_fixtures import adversarial_examples
from clinical.adversarial_model_benchmark import benchmark_adversarial
from clinical.secure_model_runner import load_config
from clinical.openai_compatible_judge import make_chat_transport

def main():
    config = load_config()
    call = make_chat_transport(endpoint=config.endpoint, model=config.model,
                               api_key=config.api_key, timeout=15)
    result = benchmark_adversarial(adversarial_examples(), call)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
