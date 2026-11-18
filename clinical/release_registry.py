"""Append-only local index of integrity-checked fictional research manifests."""
from pathlib import Path
import json
import re
from .release_manifest import verify_manifest

NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_ITEMS = 200
MAX_BYTES = 200_000

def add_manifest(directory: str | Path, release_id: str, manifest: dict) -> Path:
    if not NAME.fullmatch(release_id):
        raise ValueError("Invalid release identifier")
    if not verify_manifest(manifest):
        raise ValueError("Invalid manifest checksum")
    root = Path(directory)
    if root.is_symlink():
        raise ValueError("Registry directory cannot be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    target = root / (release_id + ".json")
    # Exclusive creation protects existing records; registry is local, not tamper-proof.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return target

def list_manifests(directory: str | Path, *, decision: str | None = None,
                   commit_sha: str | None = None) -> dict:
    if decision is not None and decision not in ("pending", "approved", "rejected"):
        raise ValueError("Invalid decision filter")
    if commit_sha is not None and not re.fullmatch(r"[a-f0-9]{40}", commit_sha):
        raise ValueError("Invalid commit SHA filter")
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Registry directory unavailable")
    files = sorted(root.glob("*.json"))
    if len(files) > MAX_ITEMS:
        raise ValueError("Registry size limit exceeded")
    records = []
    for path in files:
        if path.is_symlink() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid registry entry")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if not verify_manifest(manifest):
            raise ValueError("Corrupt registry manifest")
        review = manifest["manual_review"]
        if decision is not None and review["decision"] != decision:
            continue
        if commit_sha is not None and manifest["commit_sha"] != commit_sha:
            continue
        records.append({
            "release_id": path.stem,
            "commit_sha": manifest["commit_sha"],
            "recorded_at": manifest["recorded_at"],
            "manifest_sha256": manifest["manifest_sha256"],
            "report_sha256": manifest["report_sha256"],
            "quality_status": manifest["quality_status"],
            "readiness_status": manifest["readiness_status"],
            "decision": review["decision"],
            "blockers": manifest["readiness_blockers"],
        })
    return {"count": len(records), "releases": records,
            "disclaimer": "Local integrity-checked research records; not authenticated approval or clinical validation."}
