"""Deterministic, privacy-minimized synthetic evaluation report."""
from dataclasses import asdict
from hashlib import sha256
import json

from .adversarial_fixtures import adversarial_examples
from .adversarial_evaluation import evaluate_adversarial
from .benchmark_quality_gates import QualityThresholds, assess_quality
from .human_adjudication import Review, adjudication_report
from .reviewer_reliability import reliability_report

SCHEMA_VERSION = "1.0"

def _canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("utf-8")

def _digest(data: object) -> str:
    return sha256(_canonical(data)).hexdigest()

def build_report(reviews: tuple[Review, ...], thresholds: QualityThresholds | None = None,
                 *, experiment_id: str | None = None) -> dict:
    """Build stable output from inputs, excluding reviewer identities, notes and timestamps."""
    if experiment_id is not None and (not isinstance(experiment_id, str) or
                                      not 1 <= len(experiment_id) <= 64 or
                                      not all(c.isalnum() or c in "-_" for c in experiment_id)):
        raise ValueError("Invalid experiment identifier")
    examples = adversarial_examples()
    fixtures = [
        {"id": e.example_id, "category": e.category, "claim": e.claim.text,
         "citation_ids": list(e.claim.evidence_ids),
         "evidence": [{"id": hit.document_id, "excerpt": hit.excerpt} for hit in e.evidence],
         "expected": e.expected.value}
        for e in examples
    ]
    # Pseudonymous IDs and free-text notes never enter the report. Include only
    # sorted per-case label counts in the review fingerprint.
    counts = {e.example_id: {} for e in examples}
    for review in reviews:
        if review.example_id not in counts:
            raise ValueError("Unknown synthetic example")
        bucket = counts[review.example_id]
        bucket[review.label] = bucket.get(review.label, 0) + 1
    normalized_counts = {key: dict(sorted(value.items())) for key, value in sorted(counts.items())}
    policy = thresholds or QualityThresholds()
    report = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "dataset_sha256": _digest(fixtures),
        "review_label_counts_sha256": _digest(normalized_counts),
        "fixture_count": len(fixtures),
        "review_count": len(reviews),
        "lexical_benchmark": evaluate_adversarial(examples),
        "adjudication": adjudication_report(reviews),
        "reviewer_reliability": reliability_report(reviews),
        "quality_gates": assess_quality(reviews, policy),
        "limitations": [
            "Synthetic examples and author labels are not independent clinical ground truth.",
            "Reviewer IDs are pseudonymous and self-asserted.",
            "Review fingerprint covers per-case label counts, not reviewer identities or notes.",
            "Quality gates measure review process, not clinical correctness.",
            "No external model is invoked.",
        ],
    }
    # Remove reviewer pseudonyms from pairwise results; retain aggregate kappa
    # values without identifying who provided them.
    pairs = report["reviewer_reliability"]["pairwise_cohen"]
    report["reviewer_reliability"]["pairwise_cohen"] = [
        {"paired_examples": p["paired_examples"],
         "observed_agreement": p["observed_agreement"], "kappa": p["kappa"]}
        for p in pairs
    ]
    report["report_sha256"] = _digest(report)
    return report

def verify_report(report: dict) -> bool:
    if not isinstance(report, dict) or report.get("schema_version") != SCHEMA_VERSION:
        return False
    expected = report.get("report_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        return False
    return _digest({k: v for k, v in report.items() if k != "report_sha256"}) == expected
