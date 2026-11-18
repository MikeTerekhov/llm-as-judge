"""Operator-only model evaluation on fixed synthetic fixtures.

Never use this runner for patient data. No PHI detection is provided.
"""
from dataclasses import dataclass
import os
from urllib.parse import urlparse

from .benchmark_fixtures import synthetic_examples
from .model_comparison import ComparisonReport, compare
from .openai_compatible_judge import make_chat_transport

@dataclass(frozen=True)
class RunnerConfig:
    endpoint: str
    model: str
    api_key: str
    allowed_host: str

def load_config(env: dict[str, str] | None = None) -> RunnerConfig:
    values = os.environ if env is None else env
    if values.get("AI_REGIMEN_ENABLE_MODEL_JUDGE") != "true":
        raise ValueError("Model execution disabled; explicit operator opt-in required")
    endpoint = values.get("AI_REGIMEN_MODEL_ENDPOINT", "")
    model = values.get("AI_REGIMEN_MODEL_NAME", "")
    key = values.get("AI_REGIMEN_MODEL_API_KEY", "")
    allowed_host = values.get("AI_REGIMEN_MODEL_ALLOWED_HOST", "").lower()
    parsed = urlparse(endpoint)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() != allowed_host
            or not allowed_host or parsed.username or parsed.password or parsed.query
            or parsed.fragment or parsed.port not in (None, 443)
            or not model.strip() or not key.strip()):
        raise ValueError("Invalid model configuration or endpoint host not allowlisted")
    return RunnerConfig(endpoint, model, key, allowed_host)

def run_synthetic_comparison(config: RunnerConfig, *,
                             transport_factory=make_chat_transport) -> ComparisonReport:
    """Only fixed, hardcoded fixtures are transmitted; no user-supplied claims."""
    if not config.allowed_host or urlparse(config.endpoint).hostname != config.allowed_host:
        raise ValueError("Endpoint host mismatch")
    model_call = transport_factory(endpoint=config.endpoint, model=config.model,
                                   api_key=config.api_key, timeout=15)
    return compare(synthetic_examples(), model_call)
