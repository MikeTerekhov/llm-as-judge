"""Offline synthetic comparison of lexical screener vs opt-in model verdicts."""
from dataclasses import dataclass
from typing import Callable

from .claim_judge import JudgeStatus
from .judge_benchmark import BenchmarkExample
from .llm_judge import ModelVerdict, evaluate_with_model

@dataclass(frozen=True)
class ComparisonRow:
    example_id: str
    category: str
    lexical_status: str
    model_verdict: str | None
    disposition: str
    disagreement: bool | None
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class ComparisonReport:
    total: int
    model_attempted: int
    model_returned: int
    disagreement_count: int
    disagreement_rate: float | None
    rows: tuple[ComparisonRow, ...]

def _disagrees(lexical: JudgeStatus, model: ModelVerdict) -> bool:
    """Operational disagreement, not disagreement about clinical correctness."""
    if lexical == JudgeStatus.REVIEW_REQUIRED:
        return model != ModelVerdict.SUPPORTED
    if lexical == JudgeStatus.FLAGGED:
        return model == ModelVerdict.SUPPORTED
    return False

def compare(examples: tuple[BenchmarkExample, ...],
            model_call: Callable[[str], str] | None = None) -> ComparisonReport:
    if not examples:
        raise ValueError("Comparison requires examples")
    rows = []
    returned = 0
    disagreements = 0
    attempted = 0
    for example in examples:
        # Explicit model_call is the sole opt-in switch; no default network.
        if model_call is not None:
            attempted += 1
        result = evaluate_with_model(example.claim, example.evidence, model_call)
        verdict = result.model.verdict if result.model else None
        if verdict is not None:
            returned += 1
        disagreement = _disagrees(result.lexical_status, verdict) if verdict is not None else None
        if disagreement:
            disagreements += 1
        rows.append(ComparisonRow(example.example_id, example.category,
                                  result.lexical_status.value,
                                  verdict.value if verdict else None,
                                  result.disposition, disagreement, result.reasons))
    return ComparisonReport(len(examples), attempted, returned, disagreements,
                            round(disagreements / returned, 4) if returned else None,
                            tuple(rows))
