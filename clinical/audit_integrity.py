"""POSIX-locked audit writes and separately checkpointed chain heads.

Checkpoints are trust anchors only if stored independently in protected storage.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import fcntl
import json
import os
from .research_audit import append_audit, read_audit

@contextmanager
def _lock(path: Path):
    if path.is_symlink():
        raise ValueError("Lock path cannot be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "r+") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            yield
    finally:
        # flock is released when the descriptor closes.
        pass

def _checkpoint_data(entries: tuple[dict, ...]) -> dict:
    return {"schema_version": "1.0", "sequence": len(entries),
            "head_sha256": entries[-1]["event_sha256"] if entries else None}

def checkpoint(path: str | Path, destination: str | Path) -> dict:
    """Write a new immutable checkpoint file; never overwrite existing anchors."""
    audit_path, dest = Path(path), Path(destination)
    if dest.is_symlink() or dest == audit_path:
        raise ValueError("Invalid checkpoint destination")
    with _lock(audit_path.with_suffix(audit_path.suffix + ".lock")):
        data = _checkpoint_data(read_audit(audit_path))
        data["checkpoint_sha256"] = sha256(json.dumps(data, sort_keys=True,
             separators=(",", ":")).encode()).hexdigest()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("x", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True, indent=2)
            stream.write("\n")
        return data

def verify_checkpoint(path: str | Path, checkpoint_path: str | Path) -> dict:
    dest = Path(checkpoint_path)
    if dest.is_symlink() or not dest.is_file():
        raise ValueError("Checkpoint unavailable")
    data = json.loads(dest.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "sequence",
        "head_sha256", "checkpoint_sha256"} or data["schema_version"] != "1.0":
        raise ValueError("Invalid checkpoint schema")
    digest = data["checkpoint_sha256"]
    expected = sha256(json.dumps({k:v for k,v in data.items()
        if k != "checkpoint_sha256"}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if digest != expected or not isinstance(data["sequence"], int) or data["sequence"] < 0:
        raise ValueError("Invalid checkpoint integrity")
    entries = read_audit(path)
    sequence = data["sequence"]
    if len(entries) < sequence:
        raise ValueError("Audit truncated below checkpoint")
    head = entries[sequence - 1]["event_sha256"] if sequence else None
    if head != data["head_sha256"]:
        raise ValueError("Audit history differs from checkpoint")
    return {"status": "verified", "checkpoint_sequence": sequence,
            "current_sequence": len(entries),
            "current_head_sha256": entries[-1]["event_sha256"] if entries else None,
            "disclaimer": "A checkpoint is trustworthy only if protected independently."}

def locked_append(path: str | Path, *, checkpoint_path: str | Path | None = None,
                  **event: object) -> dict:
    target = Path(path)
    with _lock(target.with_suffix(target.suffix + ".lock")):
        if checkpoint_path is not None:
            verify_checkpoint(target, checkpoint_path)
        result = append_audit(target, **event)
        # Flush appended bytes before returning. The writer lock serializes cooperative writers.
        with target.open("rb") as stream:
            os.fsync(stream.fileno())
        return result
