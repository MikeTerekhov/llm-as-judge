"""Local checksum-chained research event log, not tamper-proof provenance."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re

EVENTS = frozenset({"manifest_registered", "review_decision_recorded", "evaluation_changed"})
IDENT = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
HEX = re.compile(r"^[a-f0-9]{64}$")
MAX_EVENTS = 10000
MAX_BYTES = 5_000_000

def _digest(data: dict) -> str:
    return sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()

def _validate(entry: dict, previous: str | None, sequence: int) -> None:
    if set(entry) != {"sequence", "event_type", "release_id", "artifact_sha256",
                      "actor_id", "recorded_at", "previous_sha256", "event_sha256"}:
        raise ValueError("Invalid audit schema")
    if entry["sequence"] != sequence or entry["previous_sha256"] != previous:
        raise ValueError("Broken audit sequence or hash chain")
    if entry["event_type"] not in EVENTS or not IDENT.fullmatch(entry["release_id"]):
        raise ValueError("Invalid event type or release ID")
    if entry["actor_id"] is not None and not IDENT.fullmatch(entry["actor_id"]):
        raise ValueError("Invalid actor ID")
    if not isinstance(entry["artifact_sha256"], str) or not HEX.fullmatch(entry["artifact_sha256"]):
        raise ValueError("Invalid artifact digest")
    try:
        timestamp = datetime.fromisoformat(entry["recorded_at"])
        if timestamp.tzinfo is None:
            raise ValueError("Timezone required")
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid event timestamp") from exc
    if entry["event_sha256"] != _digest({k:v for k,v in entry.items() if k != "event_sha256"}):
        raise ValueError("Audit checksum mismatch")

def read_audit(path: str | Path) -> tuple[dict, ...]:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("Audit file cannot be a symlink")
    if not target.exists():
        return ()
    if target.stat().st_size > MAX_BYTES:
        raise ValueError("Audit file too large")
    rows = []
    previous = None
    with target.open(encoding="utf-8") as stream:
        for index, line in enumerate(stream, 1):
            if index > MAX_EVENTS:
                raise ValueError("Audit event limit exceeded")
            entry = json.loads(line)
            _validate(entry, previous, index)
            rows.append(entry)
            previous = entry["event_sha256"]
    return tuple(rows)

def append_audit(path: str | Path, *, event_type: str, release_id: str,
                 artifact_sha256: str, actor_id: str | None = None,
                 recorded_at: str | None = None) -> dict:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("Audit file cannot be a symlink")
    existing = read_audit(target)
    if len(existing) >= MAX_EVENTS:
        raise ValueError("Audit event limit exceeded")
    entry = {
        "sequence": len(existing)+1,
        "event_type": event_type,
        "release_id": release_id,
        "artifact_sha256": artifact_sha256,
        "actor_id": actor_id,
        "recorded_at": recorded_at or datetime.now(timezone.utc).isoformat(),
        "previous_sha256": existing[-1]["event_sha256"] if existing else None,
    }
    entry["event_sha256"] = _digest(entry)
    _validate(entry, entry["previous_sha256"], entry["sequence"])
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry

def audit_summary(path: str | Path, *, release_id: str | None = None) -> dict:
    if release_id is not None and not IDENT.fullmatch(release_id):
        raise ValueError("Invalid release filter")
    entries = read_audit(path)
    selected = [row for row in entries if release_id is None or row["release_id"] == release_id]
    return {"total_events": len(entries), "matched_events": len(selected),
            "chain_head_sha256": entries[-1]["event_sha256"] if entries else None,
            "events": selected,
            "disclaimer": "Hash chaining detects edits relative to a trusted head; it does not authenticate actors or prevent rewriting."}
