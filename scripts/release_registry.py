"""Local CLI to record or inspect research manifests; no deployment."""
import argparse
import json
from pathlib import Path
from clinical.release_registry import add_manifest, list_manifests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="local/release-registry")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    add.add_argument("--release-id", required=True)
    add.add_argument("--manifest", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--decision", choices=["pending", "approved", "rejected"])
    listing.add_argument("--commit-sha")
    args = parser.parse_args()
    if args.command == "add":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        print(add_manifest(args.directory, args.release_id, manifest))
    else:
        print(json.dumps(list_manifests(args.directory, decision=args.decision,
                                        commit_sha=args.commit_sha), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
