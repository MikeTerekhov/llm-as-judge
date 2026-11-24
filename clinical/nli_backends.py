"""Optional local NLI backends. Heavy dependencies are imported only when requested.

Install with `pip install -r requirements-nli.txt`. Models run locally on CPU by
default; no claim or evidence text is sent to a remote service.
"""
from .semantic_judge import NLIScorer, NLIScores

DEFAULT_NLI_MODEL = "cross-encoder/nli-deberta-v3-base"
LABELS = ("entailment", "neutral", "contradiction")

def label_indices(id2label: dict) -> dict[str, int]:
    """Map a model's output indices to NLI labels, refusing anything ambiguous."""
    mapping: dict[str, int] = {}
    for index, name in id2label.items():
        key = str(name).strip().lower()
        if key in LABELS:
            if key in mapping:
                raise ValueError(f"Duplicate NLI label {key!r}")
            mapping[key] = int(index)
    if set(mapping) != set(LABELS) or len(id2label) != len(LABELS):
        raise ValueError("Model must expose exactly entailment, neutral and contradiction labels")
    return mapping

def make_transformers_nli(model_name: str = DEFAULT_NLI_MODEL, *, revision: str | None = None,
                          local_files_only: bool = True, device: str = "cpu") -> NLIScorer:
    """Build a scorer from a Hugging Face sequence-classification NLI model.

    `local_files_only=True` by default so a benchmark run never downloads silently.
    Pin `revision` to a commit hash for reproducible results.
    """
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("NLI backend requires: pip install -r requirements-nli.txt") from exc
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision,
                                              local_files_only=local_files_only)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, revision=revision, local_files_only=local_files_only).to(device).eval()
    indices = label_indices(model.config.id2label)

    def score(premise: str, hypothesis: str) -> NLIScores:
        inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True,
                           max_length=512).to(device)
        with torch.no_grad():
            probs = torch.softmax(model(**inputs).logits[0], dim=-1).tolist()
        return NLIScores(*(round(probs[indices[label]], 6) for label in LABELS))

    return score
