"""Explicit human review gate for offline snapshots; not clinical certification."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json

from .evidence_engine import EvidenceDocument, EvidenceError


@dataclass(frozen=True)
class ReviewRecord:
    document_id: str
    sha256_digest: str
    reviewer: str
    reviewed_at: str
    source_checked: bool
    tables_checked: bool
    notes: str

    @classmethod
    def from_record(cls, data: dict):
        expected = {"document_id", "sha256_digest", "reviewer", "reviewed_at",
                    "source_checked", "tables_checked", "notes"}
        if set(data) != expected:
            raise EvidenceError("Unexpected review record fields")
        if not all(isinstance(data[k], str) and data[k].strip()
                   for k in ("document_id", "sha256_digest", "reviewer", "reviewed_at")):
            raise EvidenceError("Missing review identity or timestamp")
        if not isinstance(data["notes"], str):
            raise EvidenceError("Review notes must be text")
        if type(data["source_checked"]) is not bool or type(data["tables_checked"]) is not bool:
            raise EvidenceError("Review flags must be booleans")
        try:
            when = datetime.fromisoformat(data["reviewed_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvidenceError("Invalid review timestamp") from exc
        if when.tzinfo is None or when.utcoffset() is None:
            raise EvidenceError("Review timestamp must include timezone")
        return cls(**data)


def approved_documents(documents: list[EvidenceDocument], reviews: list[ReviewRecord]) -> list[EvidenceDocument]:
    """Fail closed unless a matching snapshot was explicitly reviewed.

    This gate checks operator attestations, not reviewer credentials or clinical validity.
    """
    if len({d.document_id for d in documents}) != len(documents):
        raise EvidenceError("Duplicate document IDs")
    if len({r.document_id for r in reviews}) != len(reviews):
        raise EvidenceError("Duplicate review IDs")
    approved = []
    by_id = {r.document_id: r for r in reviews}
    for doc in documents:
        review = by_id.get(doc.document_id)
        if not review or not (review.source_checked and review.tables_checked):
            continue
        if review.sha256_digest != doc.sha256_digest:
            continue
        reviewed_at = datetime.fromisoformat(review.reviewed_at.replace("Z", "+00:00"))
        if reviewed_at < doc.retrieved_at:
            continue
        approved.append(doc)
    return approved


def load_approved_index(snapshot_path: str, review_path: str, max_age_days: int = 180):
    from .evidence_engine import LocalEvidenceIndex
    index = LocalEvidenceIndex.from_json(snapshot_path, max_age_days=max_age_days)
    with open(review_path, encoding="utf-8") as stream:
        records = json.load(stream)
    if not isinstance(records, list):
        raise EvidenceError("Expected review JSON array")
    reviews = [ReviewRecord.from_record(r) for r in records]
    return LocalEvidenceIndex(approved_documents(list(index.documents), reviews), max_age_days=max_age_days)
