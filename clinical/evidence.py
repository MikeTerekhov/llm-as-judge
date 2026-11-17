"""Evidence interfaces; no fabricated citations or live retrieval."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EvidenceSource:
    title: str
    url: str
    version: str
    retrieved_at: str
    excerpt: str


class EvidenceProvider(Protocol):
    def search(self, query: str) -> list[EvidenceSource]:
        """Return verifiable, versioned sources; never synthesize citations."""
        ...


class EmptyEvidenceProvider:
    def search(self, query: str) -> list[EvidenceSource]:
        return []
