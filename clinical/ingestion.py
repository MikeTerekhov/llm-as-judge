"""Constrained guideline snapshot ingestion for offline human review.

Source text is untrusted. No automatic clinical endorsement or treatment advice.
"""
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import json

from .evidence_engine import EvidenceDocument, EvidenceError, TRUSTED_HOSTS
from .structured_html import extract_structured_text

MAX_BYTES = 1_000_000
MAX_TEXT = 200_000

class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EvidenceError("Redirects are disabled; review the new URL manually")

class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            self.skip_depth += 1
        elif tag in self.SKIP:
            self.skip_depth = 1
        elif tag in {"p", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
        elif tag in {"p", "h1", "h2", "h3", "li"}:
            self.parts.append("\n\n")
    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname not in TRUSTED_HOSTS or
            parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment):
        raise EvidenceError("URL must be an approved HTTPS guideline page without query or fragment")

def fetch_guideline(url: str) -> str:
    validate_url(url)
    opener = build_opener(NoRedirects)
    request = Request(url, headers={"User-Agent": "AI-Regimen-Research-Snapshot/0.5",
                                    "Accept": "text/html"})
    with opener.open(request, timeout=15) as response:
        if response.status != 200:
            raise EvidenceError("Unexpected HTTP status")
        if "text/html" not in response.headers.get("Content-Type", "").lower():
            raise EvidenceError("Expected HTML guideline page")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise EvidenceError("Source exceeds size limit")
        charset = response.headers.get_content_charset() or "utf-8"
        if charset.lower() not in {"utf-8", "utf8"}:
            raise EvidenceError("Unsupported source encoding")
    text = extract_structured_text(raw.decode("utf-8", errors="strict"))
    if not text or len(text) > MAX_TEXT:
        raise EvidenceError("Empty or oversized extracted text")
    return text

def build_snapshot(*, document_id: str, title: str, url: str,
                   version: str, published_on: str, content: str,
                   retrieved_at: datetime | None = None) -> dict:
    """Metadata is operator-supplied and requires manual source verification."""
    validate_url(url)
    now = retrieved_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise EvidenceError("Retrieval timestamp must be timezone-aware")
    record = dict(document_id=document_id, title=title, url=url, version=version,
                  published_on=published_on, retrieved_at=now.isoformat(),
                  content=content, sha256_digest=sha256(content.encode("utf-8")).hexdigest())
    EvidenceDocument.from_record(record)
    return record

def write_snapshot(path: str, record: dict) -> None:
    """Single-document snapshot; do not commit copyrighted source text blindly."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump([record], handle, indent=2, ensure_ascii=False)
