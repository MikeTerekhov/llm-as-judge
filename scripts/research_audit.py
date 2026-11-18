"""Local research audit event CLI; no network calls or deployments."""
import argparse
import json
from clinical.research_audit import audit_summary
from clinical.audit_integrity import locked_append

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="local/research-audit.jsonl")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("append")
    add.add_argument("--event-type", required=True,
                     choices=["manifest_registered", "review_decision_recorded", "evaluation_changed"])
    add.add_argument("--release-id", required=True)
    add.add_argument("--artifact-sha256", required=True)
    add.add_argument("--actor-id")
    show = commands.add_parser("list")
    show.add_argument("--release-id")
    args = parser.parse_args()
    if args.command == "append":
        print(json.dumps(locked_append(args.path, event_type=args.event_type,
                                     release_id=args.release_id,
                                     artifact_sha256=args.artifact_sha256,
                                     actor_id=args.actor_id), indent=2))
    else:
        print(json.dumps(audit_summary(args.path, release_id=args.release_id), indent=2))

if __name__ == "__main__":
    main()
