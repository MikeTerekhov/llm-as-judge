"""POSIX local audit append, checkpoint and verification CLI."""
import argparse
import json
from clinical.audit_integrity import locked_append, checkpoint, verify_checkpoint

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="local/research-audit.jsonl")
    commands = parser.add_subparsers(dest="command", required=True)
    append = commands.add_parser("append")
    append.add_argument("--event-type", required=True,
                        choices=["manifest_registered", "review_decision_recorded", "evaluation_changed"])
    append.add_argument("--release-id", required=True)
    append.add_argument("--artifact-sha256", required=True)
    append.add_argument("--actor-id")
    append.add_argument("--checkpoint")
    create = commands.add_parser("checkpoint")
    create.add_argument("--output", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--checkpoint", required=True)
    args = parser.parse_args()
    if args.command == "append":
        result = locked_append(args.path, checkpoint_path=args.checkpoint,
                               event_type=args.event_type, release_id=args.release_id,
                               artifact_sha256=args.artifact_sha256, actor_id=args.actor_id)
    elif args.command == "checkpoint":
        result = checkpoint(args.path, args.output)
    else:
        result = verify_checkpoint(args.path, args.checkpoint)
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
