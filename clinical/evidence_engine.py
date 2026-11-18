"""Offline versioned evidence retrieval. No clinical inference or live fetching."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from urllib.parse import urlparse
import json
import re

TRUSTED_HOSTS = frozenset({"clinicalinfo.hiv.gov", "hivinfo.nih.gov", "accessdata.fda.gov", "fda.gov", "www.fda.gov"})
TOKEN = re.compile(r"[a-z0-9]+")

class EvidenceError(ValueError):
    pass

@dataclass(frozen=True)
class EvidenceDocument:
    document_id: str
    title: str
    url: str
    version: str
    published_on: date
    retrieved_at: datetime
    content: str
    sha256_digest: str

    @classmethod
    def from_record(cls, record: dict):
        required = {"document_id", "title", "url", "version", "published_on", "retrieved_at", "content", "sha256_digest"}
        if set(record) != required:
            raise EvidenceError("Unexpected evidence record fields")
        parsed = urlparse(record["url"])
        if (parsed.scheme != "https" or parsed.hostname not in TRUSTED_HOSTS or
                parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment):
            raise EvidenceError("Untrusted source URL")
        for key in ("document_id", "title", "version", "content"):
            if not isinstance(record[key], str) or not record[key].strip():
                raise EvidenceError(f"Invalid {key}")
        try:
            published = date.fromisoformat(record["published_on"])
            retrieved = datetime.fromisoformat(record["retrieved_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError) as exc:
            raise EvidenceError("Invalid date") from exc
        if retrieved.tzinfo is None or retrieved.utcoffset() is None or published > retrieved.date():
            raise EvidenceError("Invalid date chronology or timezone")
        digest = sha256(record["content"].encode("utf-8")).hexdigest()
        if digest != record["sha256_digest"]:
            raise EvidenceError("Content integrity check failed")
        return cls(record["document_id"], record["title"], record["url"], record["version"],
                   published, retrieved, record["content"], digest)

@dataclass(frozen=True)
class EvidenceHit:
    document_id: str
    title: str
    url: str
    version: str
    published_on: str
    retrieved_at: str
    sha256_digest: str
    excerpt: str
    score: int

class LocalEvidenceIndex:
    """Search locally supplied snapshots, rejecting stale evidence."""
    def __init__(self, documents: list[EvidenceDocument], max_age_days: int = 180):
        if max_age_days < 0 or len({d.document_id for d in documents}) != len(documents):
            raise EvidenceError("Invalid max age or duplicate document IDs")
        self.documents = tuple(documents)
        self.max_age_days = max_age_days

    @classmethod
    def from_json(cls, path: str, max_age_days: int = 180):
        with open(path, encoding="utf-8") as stream:
            records = json.load(stream)
        if not isinstance(records, list):
            raise EvidenceError("Expected JSON array")
        return cls([EvidenceDocument.from_record(r) for r in records], max_age_days)

    def search(self, query: str, *, as_of: date | None = None, limit: int = 5) -> list[EvidenceHit]:
        if limit < 1:
            raise EvidenceError("limit must be positive")
        as_of = as_of or datetime.now(timezone.utc).date()
        terms = set(TOKEN.findall(query.lower()))
        if not terms:
            return []
        hits = []
        for doc in self.documents:
            age = (as_of - doc.retrieved_at.date()).days
            if not 0 <= age <= self.max_age_days or doc.published_on > as_of:
                continue
            paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
            ranked = sorted(((len(terms & set(TOKEN.findall(p.lower()))), p) for p in paragraphs), reverse=True)
            if not ranked or ranked[0][0] == 0:
                continue
            score, paragraph = ranked[0]
            hits.append(EvidenceHit(doc.document_id, doc.title, doc.url, doc.version,
                                    doc.published_on.isoformat(), doc.retrieved_at.isoformat(),
                                    doc.sha256_digest, paragraph[:800], score))
        return sorted(hits, key=lambda h: (-h.score, h.document_id))[:limit]
