"""Local, synthetic-only reviewer labels and disagreement analysis."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from .adversarial_fixtures import SemanticLabel, adversarial_examples

IDENT = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
VALID_IDS = frozenset(e.example_id for e in adversarial_examples())

@dataclass(frozen=True)
class Review:
    example_id: str
    reviewer_id: str
    label: str
    note: str
    reviewed_at: str

def make_review(example_id: str, reviewer_id: str, label: str, note: str = "") -> Review:
    if example_id not in VALID_IDS or not IDENT.fullmatch(reviewer_id):
        raise ValueError("Unknown synthetic example or invalid reviewer ID")
    SemanticLabel(label)
    if not isinstance(note, str) or len(note) > 300:
        raise ValueError("Review note must be at most 300 characters")
    return Review(example_id, reviewer_id, label, note, datetime.now(timezone.utc).isoformat())

def append_review(path: str | Path, review: Review) -> None:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("Review path must not be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        for existing in read_reviews(target):
            if (existing.example_id, existing.reviewer_id) == (review.example_id, review.reviewer_id):
                raise ValueError("Reviewer already labeled this example")
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(review), sort_keys=True) + "\n")

def read_reviews(path: str | Path) -> tuple[Review, ...]:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("Review path must not be a symlink")
    if not target.exists():
        return ()
    reviews = []
    with target.open(encoding="utf-8") as stream:
        for line in stream:
            raw = json.loads(line)
            if set(raw) != set(Review.__dataclass_fields__):
                raise ValueError("Unexpected review schema")
            if raw["example_id"] not in VALID_IDS or not IDENT.fullmatch(raw["reviewer_id"]):
                raise ValueError("Invalid stored review identifier")
            SemanticLabel(raw["label"])
            reviews.append(Review(**raw))
    return tuple(reviews)

def adjudication_report(reviews: tuple[Review, ...]) -> dict:
    grouped: dict[str, dict[str, str]] = {}
    for review in reviews:
        by_reviewer = grouped.setdefault(review.example_id, {})
        if review.reviewer_id in by_reviewer:
            raise ValueError("Duplicate reviewer/example pair")
        by_reviewer[review.reviewer_id] = review.label
    rows = []
    agreed = 0
    comparable = 0
    for example in adversarial_examples():
        votes = grouped.get(example.example_id, {})
        labels = set(votes.values())
        has_multiple = len(votes) >= 2
        consensus = next(iter(labels)) if has_multiple and len(labels) == 1 else None
        if has_multiple:
            comparable += 1
            agreed += int(consensus is not None)
        rows.append({"example_id": example.example_id, "category": example.category,
                     "reviewers": len(votes), "consensus": consensus,
                     "disputed": has_multiple and len(labels) > 1,
                     "needs_second_review": len(votes) < 2})
    return {"total_examples": len(rows), "reviewed_examples": sum(r["reviewers"] > 0 for r in rows),
            "multiply_reviewed": comparable, "unanimous_count": agreed,
            "unanimity_rate": round(agreed / comparable, 4) if comparable else None,
            "rows": rows,
            "disclaimer": "Unanimity is not accuracy; labels are for fictional research fixtures only."}
