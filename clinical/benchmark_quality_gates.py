"""Conservative quality gates for fictional benchmark annotations.

These are research process checks, not clinical validation or truth guarantees.
"""
from dataclasses import asdict, dataclass
from .human_adjudication import Review, adjudication_report
from .reviewer_reliability import reliability_report

@dataclass(frozen=True)
class QualityThresholds:
    min_review_coverage: float = 1.0
    min_double_review_coverage: float = 1.0
    max_disputed_fraction: float = 0.0
    min_pairwise_kappa: float = 0.6

    def __post_init__(self):
        for field in ("min_review_coverage", "min_double_review_coverage",
                      "max_disputed_fraction"):
            value = getattr(self, field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                raise ValueError("Invalid coverage or dispute threshold")
        if (not isinstance(self.min_pairwise_kappa, (int, float)) or
                isinstance(self.min_pairwise_kappa, bool) or not -1 <= self.min_pairwise_kappa <= 1):
            raise ValueError("Invalid kappa threshold")

def assess_quality(reviews: tuple[Review, ...],
                   thresholds: QualityThresholds | None = None) -> dict:
    policy = thresholds or QualityThresholds()
    summary = adjudication_report(reviews)
    reliability = reliability_report(reviews)
    total = summary["total_examples"]
    reviewed = summary["reviewed_examples"]
    doubled = summary["multiply_reviewed"]
    disputed = sum(row["disputed"] for row in summary["rows"])
    review_coverage = reviewed / total if total else 0.0
    double_coverage = doubled / total if total else 0.0
    disputed_fraction = disputed / doubled if doubled else None
    pairs = reliability["pairwise_cohen"]
    defined = [pair["kappa"] for pair in pairs if pair["kappa"] is not None]
    undefined = [pair for pair in pairs if pair["kappa"] is None]
    checks = [
        {"name": "review_coverage", "passed": review_coverage >= policy.min_review_coverage,
         "observed": round(review_coverage, 4), "threshold": policy.min_review_coverage},
        {"name": "double_review_coverage", "passed": double_coverage >= policy.min_double_review_coverage,
         "observed": round(double_coverage, 4), "threshold": policy.min_double_review_coverage},
        {"name": "dispute_fraction", "passed": disputed_fraction is not None and
         disputed_fraction <= policy.max_disputed_fraction,
         "observed": round(disputed_fraction, 4) if disputed_fraction is not None else None,
         "threshold": policy.max_disputed_fraction},
        {"name": "pairwise_kappa", "passed": bool(pairs) and not undefined and
         bool(defined) and min(defined) >= policy.min_pairwise_kappa,
         "observed": round(min(defined), 4) if defined else None,
         "threshold": policy.min_pairwise_kappa},
    ]
    return {"status": "pass" if all(check["passed"] for check in checks) else "blocked",
            "checks": checks, "thresholds": asdict(policy),
            "reviewed_examples": reviewed, "multiply_reviewed": doubled,
            "disputed_examples": disputed,
            "disclaimer": "Passing gates does not establish semantic or clinical correctness."}
