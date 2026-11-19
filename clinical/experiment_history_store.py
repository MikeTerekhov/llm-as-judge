"""Local synthetic benchmark history with atomic, append-only-in-practice writes.

No network, no patient data, no API routes. Intended for one local writer.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

from clinical.adversarial_fixtures import adversarial_examples
from clinical.model_run_comparison import _validate_run

MAX_HISTORY_BYTES = 2 * 1024 * 1024
MAX_RUNS = 200

def _canonical(run: dict) -> str:
    return json.dumps(run, sort_keys=True, separators=(",", ":"), allow_nan=False)

def validate_run(run: dict) -> None:
    rows = _validate_run(run)
    expected = {e.example_id: e.expected.value for e in adversarial_examples()}
    if {identifier: label for identifier, (label, _) in rows.items()} != expected:
        raise ValueError("Report fixtures do not match the current fictional benchmark")

def read_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    if path.stat().st_size > MAX_HISTORY_BYTES:
        raise ValueError("History file exceeds size limit")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("runs"), list):
        raise ValueError("Unsupported history schema")
    if len(data["runs"]) > MAX_RUNS:
        raise ValueError("History has too many runs")
    for entry in data["runs"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("recorded_at"), str) or not isinstance(entry.get("sha256"), str):
            raise ValueError("Invalid history entry")
        validate_run(entry.get("run"))
        if hashlib.sha256(_canonical(entry["run"]).encode()).hexdigest() != entry["sha256"]:
            raise ValueError("History entry checksum mismatch")
    return data["runs"]

def append_run(path: Path, run: dict, *, recorded_at: str | None = None) -> dict:
    validate_run(run)
    history = read_history(path)
    if len(history) >= MAX_RUNS:
        raise ValueError("History has reached the run limit")
    digest = hashlib.sha256(_canonical(run).encode()).hexdigest()
    if any(entry["sha256"] == digest for entry in history):
        raise ValueError("Identical benchmark report already saved")
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat()
    parsed = datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    entry = {"recorded_at": timestamp, "sha256": digest, "run": run}
    payload = json.dumps({"schema_version": 1, "runs": [*history, entry]},
                         sort_keys=True, indent=2, allow_nan=False) + "\n"
    if len(payload.encode("utf-8")) > MAX_HISTORY_BYTES:
        raise ValueError("History would exceed size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".history-", suffix=".tmp", delete=False) as stream:
            temp_path = Path(stream.name)
            os.chmod(temp_path, 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return {"recorded_at": timestamp, "sha256": digest, "model": run["model"], "run_count": len(history)+1}

def history_summary(entries: list[dict]) -> list[dict]:
    output = []
    for entry in entries:
        rows = entry["run"]["report"]["rows"]
        evaluated = [r for r in rows if r["model_verdict"] is not None]
        matched = sum(r["expected"] == r["model_verdict"] for r in evaluated)
        output.append({"recorded_at": entry["recorded_at"], "model": entry["run"]["model"],
                       "sha256": entry["sha256"], "returned": len(evaluated),
                       "coverage": round(len(evaluated)/len(rows), 4),
                       "conditional_agreement": round(matched/len(evaluated), 4) if evaluated else None})
    return sorted(output, key=lambda row: (row["recorded_at"], row["sha256"]))
