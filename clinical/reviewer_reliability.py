"""Inter-rater reliability for fictional benchmark annotations.

Kappa measures consistency, not correctness. Undefined values remain null.
"""
from collections import Counter, defaultdict
from itertools import combinations
from .adversarial_fixtures import SemanticLabel, adversarial_examples
from .human_adjudication import Review

LABELS = tuple(label.value for label in SemanticLabel)

def _kappa(observed: float, expected: float) -> float | None:
    if abs(1 - expected) < 1e-12:
        return None
    return round((observed - expected) / (1 - expected), 4)

def cohen_kappa(left: dict[str, str], right: dict[str, str]) -> dict:
    """Compute Cohen's kappa on the intersection of example IDs."""
    shared = sorted(set(left) & set(right))
    if not shared:
        return {"paired_examples": 0, "observed_agreement": None, "kappa": None}
    for example_id in shared:
        if left[example_id] not in LABELS or right[example_id] not in LABELS:
            raise ValueError("Unknown semantic label")
    n = len(shared)
    observed = sum(left[x] == right[x] for x in shared) / n
    left_counts = Counter(left[x] for x in shared)
    right_counts = Counter(right[x] for x in shared)
    expected = sum(left_counts[label] * right_counts[label] for label in LABELS) / (n*n)
    return {"paired_examples": n, "observed_agreement": round(observed, 4),
            "kappa": _kappa(observed, expected)}

def fleiss_kappa(votes: dict[str, tuple[str, ...]]) -> dict:
    """Classic Fleiss kappa; requires >=2 raters and equal ratings per item."""
    if not votes:
        return {"items": 0, "raters_per_item": None, "kappa": None}
    sizes = {len(v) for v in votes.values()}
    if len(sizes) != 1 or min(sizes) < 2:
        return {"items": len(votes), "raters_per_item": None, "kappa": None}
    raters = sizes.pop()
    for labels in votes.values():
        if any(label not in LABELS for label in labels):
            raise ValueError("Unknown semantic label")
    n = len(votes)
    category_totals = Counter(label for item in votes.values() for label in item)
    p = {label: category_totals[label] / (n*raters) for label in LABELS}
    expected = sum(value*value for value in p.values())
    per_item = []
    for labels in votes.values():
        counts = Counter(labels)
        per_item.append((sum(counts[label]**2 for label in LABELS)-raters) /
                        (raters*(raters-1)))
    observed = sum(per_item)/n
    return {"items": n, "raters_per_item": raters,
            "observed_agreement": round(observed, 4),
            "kappa": _kappa(observed, expected)}

def reliability_report(reviews: tuple[Review, ...]) -> dict:
    examples = {example.example_id: example for example in adversarial_examples()}
    by_reviewer: dict[str, dict[str, str]] = defaultdict(dict)
    by_item: dict[str, dict[str, str]] = defaultdict(dict)
    for review in reviews:
        if review.example_id not in examples or review.label not in LABELS:
            raise ValueError("Invalid review")
        if review.example_id in by_reviewer[review.reviewer_id]:
            raise ValueError("Duplicate reviewer/example pair")
        by_reviewer[review.reviewer_id][review.example_id] = review.label
        by_item[review.example_id][review.reviewer_id] = review.label
    pairs = []
    for left, right in combinations(sorted(by_reviewer), 2):
        metric = cohen_kappa(by_reviewer[left], by_reviewer[right])
        if metric["paired_examples"]:
            pairs.append({"reviewer_a": left, "reviewer_b": right, **metric})
    eligible = {key: tuple(votes.values()) for key, votes in by_item.items() if len(votes) >= 2}
    fleiss = fleiss_kappa(eligible)
    categories: dict[str, dict[str, int]] = defaultdict(lambda: {"reviewed":0,"multiply_reviewed":0,"disputed":0})
    for example_id, votes in by_item.items():
        counts = categories[examples[example_id].category]
        counts["reviewed"] += 1
        if len(votes) >= 2:
            counts["multiply_reviewed"] += 1
            counts["disputed"] += int(len(set(votes.values())) > 1)
    return {"reviewer_count": len(by_reviewer), "pairwise_cohen": pairs,
            "fleiss": fleiss, "categories": dict(sorted(categories.items())),
            "disclaimer": "Inter-rater consistency is not clinical or semantic accuracy."}
