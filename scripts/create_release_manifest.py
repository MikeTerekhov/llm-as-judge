"""Create a local research release manifest; never deploys or publishes."""
import argparse
import json
from pathlib import Path
from clinical.release_manifest import build_manifest, verify_manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--regression")
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--reviewer-id")
    parser.add_argument("--approval", choices=["pending", "approved", "rejected"], default="pending")
    parser.add_argument("--output", default="local/release-manifest.json")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    regression = json.loads(Path(args.regression).read_text(encoding="utf-8")) if args.regression else None
    manifest = build_manifest(report, regression, commit_sha=args.commit_sha,
                              reviewer_id=args.reviewer_id, approval=args.approval)
    if not verify_manifest(manifest):
        raise RuntimeError("Manifest checksum verification failed")
    target = Path(args.output)
    if target.is_symlink():
        raise ValueError("Output path cannot be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Research manifest: {target} decision={args.approval} sha256={manifest['manifest_sha256']}")

if __name__ == "__main__":
    main()
