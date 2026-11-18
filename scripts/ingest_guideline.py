"""Explicit, manual guideline snapshot ingestion. No background crawling."""
import argparse
from clinical.ingestion import fetch_guideline, build_snapshot, write_snapshot

def main():
    parser = argparse.ArgumentParser(description="Create a research-only guideline snapshot for manual verification")
    parser.add_argument("--url", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--version", required=True, help="Manually verified guideline revision")
    parser.add_argument("--published-on", required=True, help="Manually verified YYYY-MM-DD")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    content = fetch_guideline(args.url)
    record = build_snapshot(document_id=args.document_id, title=args.title, url=args.url,
                            version=args.version, published_on=args.published_on, content=content)
    write_snapshot(args.output, record)
    print("Snapshot written for manual verification. NOT authenticated or clinically approved.")

if __name__ == "__main__":
    main()
