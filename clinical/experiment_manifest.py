"""Reproducible, secret-free manifests for fictional LLM evaluation runs.

Metadata is operator-declared, not independently verified provider provenance.
"""
from datetime import datetime, timezone
import hashlib
import json
import re

from clinical.experiment_history_store import _canonical, validate_run

SCHEMA_VERSION = 1
SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")
MAX_NOTES = 500

def _identifier(value: str, name: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"{name} must be 1-80 safe characters")
    return value

def build_manifest(run: dict, *, experiment_id: str, model_version: str,
                   dataset_version: str = "synthetic-adversarial-v1",
                   prompt_version: str = "llm-judge-v1",
                   notes: str = "", recorded_at: str | None = None) -> dict:
    validate_run(run)
    for name, value in (("experiment_id", experiment_id), ("model_version", model_version),
                        ("dataset_version", dataset_version), ("prompt_version", prompt_version)):
        _identifier(value, name)
    if not isinstance(notes, str) or len(notes) > MAX_NOTES:
        raise ValueError("Notes exceed 500 characters")
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat()
    try:
        date = datetime.fromisoformat(timestamp)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid timestamp") from exc
    if date.tzinfo is None:
        raise ValueError("Timestamp requires timezone")
    report_hash = hashlib.sha256(_canonical(run).encode("utf-8")).hexdigest()
    return {"schema_version": SCHEMA_VERSION, "experiment_id": experiment_id,
            "recorded_at": timestamp, "model": run["model"],
            "model_version": model_version, "dataset_version": dataset_version,
            "prompt_version": prompt_version, "report_sha256": report_hash,
            "fixture_count": 12, "notes": notes,
            "disclaimer": "Operator-declared research metadata for fictional fixtures; not provider attestation or clinical validation."}

def verify_manifest(manifest: dict, run: dict) -> bool:
    validate_run(run)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported manifest schema")
    for key in ("experiment_id", "model_version", "dataset_version", "prompt_version"):
        _identifier(manifest.get(key), key)
    if manifest.get("model") != run["model"] or manifest.get("fixture_count") != 12:
        raise ValueError("Manifest model or fixture count mismatch")
    expected = hashlib.sha256(_canonical(run).encode("utf-8")).hexdigest()
    if manifest.get("report_sha256") != expected:
        raise ValueError("Manifest report checksum mismatch")
    return True
