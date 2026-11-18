"""Offline synthetic benchmark for conservative claim screening.

Benchmark labels describe lexical-screen expectations, not clinical truth.
"""
from dataclasses import dataclass
from typing import Iterable
from .assessment import Claim
from .claim_judge import JudgeStatus, judge_claim
from .evidence_engine import EvidenceHit

@dataclass(frozen=True)
class BenchmarkExample:
    example_id: str
    claim: Claim
    evidence: tuple[EvidenceHit, ...]
    expected: JudgeStatus
    category: str

@dataclass(frozen=True)
class BenchmarkResult:
    total: int
    correct: int
    accuracy: float
    confusion: dict[str, dict[str, int]]
    per_category: dict[str, dict[str, float | int]]

def evaluate(examples: Iterable[BenchmarkExample]) -> BenchmarkResult:
    rows = tuple(examples)
    if not rows:
        raise ValueError("Benchmark must not be empty")
    ids = [row.example_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate benchmark IDs")
    confusion: dict[str, dict[str, int]] = {}
    categories: dict[str, list[bool]] = {}
    correct = 0
    for row in rows:
        predicted = judge_claim(row.claim, row.evidence).status
        confusion.setdefault(row.expected.value, {})
        confusion[row.expected.value][predicted.value] = confusion[row.expected.value].get(predicted.value, 0) + 1
        is_correct = predicted == row.expected
        correct += is_correct
        categories.setdefault(row.category, []).append(is_correct)
    return BenchmarkResult(len(rows), correct, round(correct / len(rows), 4),
                           confusion, {name: {"count": len(scores),
                                              "accuracy": round(sum(scores) / len(scores), 4)}
                                       for name, scores in sorted(categories.items())})
