"""DistilBERT scam classifier - the optional deep-learning upgrade to Model 1.

The TF-IDF + Logistic Regression model (``scam_predictor.py``) is fast, tiny and
perfectly interpretable. DistilBERT trades size for contextual understanding: it
reads word *order* and *meaning*, catching scams that dodge keyword models
("kindly revalidate your account to avoid deactivation").

Design so the rest of the package never pays for it
---------------------------------------------------
* ``torch`` / ``transformers`` are imported LAZILY, inside functions. Importing
  this module (or the whole package) works with neither installed - only calling
  into it requires them. So the CPU-only production image stays slim and the
  linear model keeps serving until you deliberately enable this path.
* Enable it with ONE command (run it on a stable connection - torch is ~2GB):
      uv pip install -e ".[transformers]"        # from ml/
  then fine-tune:
      python -m snaija_ml.pipelines.train_scam_transformer
  Artifacts land in ``models/scam_transformer/`` and this class serves them.

The prediction contract mirrors ``ScamPrediction`` (label / probability /
confidence / highlighted_words / explanation) so it is a drop-in replacement:
callers depend on the contract, not the algorithm. Word highlighting uses
occlusion (mask a token, measure the probability drop) - model-agnostic and
needs no gradients.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .scam_predictor import HighlightedWord, ScamPrediction

REGISTRY_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_BASE_MODEL = "distilbert-base-uncased"

# Same two-threshold banding as the linear model, for a consistent UX.
SUSPICIOUS_THRESHOLD = 0.40
SCAM_THRESHOLD = 0.70


def transformers_available() -> bool:
    """True if torch + transformers can be imported (no heavy work done)."""
    import importlib.util as u

    return bool(u.find_spec("torch") and u.find_spec("transformers"))


def _require_transformers() -> None:
    if not transformers_available():
        raise RuntimeError(
            "DistilBERT path needs torch + transformers. Install once on a stable "
            "connection:  uv pip install -e \".[transformers]\"  (from ml/), then "
            "run:  python -m snaija_ml.pipelines.train_scam_transformer"
        )


class ScamTransformer:
    """Serves a fine-tuned DistilBERT scam classifier from the model registry."""

    def __init__(self, registry_dir: Path | None = None) -> None:
        _require_transformers()
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_dir = (registry_dir or REGISTRY_DIR) / "scam_transformer"
        if not model_dir.exists():
            raise RuntimeError(
                f"No fine-tuned model at {model_dir}. Train it first: "
                "python -m snaija_ml.pipelines.train_scam_transformer"
            )
        self._torch = torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._tok = AutoTokenizer.from_pretrained(str(model_dir))
        self._model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
        self._model.to(self._device).eval()
        self.version = "distilbert-1.0.0"

    def _scam_proba(self, text: str) -> float:
        torch = self._torch
        enc = self._tok(text, truncation=True, max_length=128, return_tensors="pt").to(self._device)
        with torch.no_grad():
            logits = self._model(**enc).logits
            proba = torch.softmax(logits, dim=-1)[0, 1].item()
        return float(proba)

    def predict(self, message: str, top_k: int = 6) -> ScamPrediction:
        proba = self._scam_proba(message)
        label = ("Scam" if proba >= SCAM_THRESHOLD
                 else "Suspicious" if proba >= SUSPICIOUS_THRESHOLD else "Safe")
        highlights = self._highlight(message, proba, top_k)
        pct = round(proba * 100)
        words = ", ".join(f'"{h.word}"' for h in highlights[:3])
        if label == "Scam":
            explanation = (f"Scam ({pct}% risk)." + (f" Note {words}." if words else "")
                           + " Do not click links, call numbers, or share BVN/OTP/PIN.")
        elif label == "Suspicious":
            explanation = (f"Suspicious ({pct}% risk) - verify via an official channel."
                           + (f" It emphasises {words}." if words else ""))
        else:
            explanation = f"Looks safe ({pct}% risk). Never share your BVN, OTP or PIN."

        return ScamPrediction(
            label=label,
            scam_probability=round(proba, 4),
            confidence=round(max(proba, 1 - proba), 4),
            highlighted_words=highlights,
            explanation=explanation,
            model_version=self.version,
        )

    def _highlight(self, message: str, base_proba: float, top_k: int) -> list[HighlightedWord]:
        """Occlusion attribution: drop each word, measure how far scam risk falls."""
        words = message.split()
        if len(words) < 2:
            return []
        scored: list[tuple[str, float]] = []
        for i, w in enumerate(words):
            occluded = " ".join(words[:i] + words[i + 1:])
            drop = base_proba - self._scam_proba(occluded)
            if drop > 0:
                scored.append((w, drop))
        scored.sort(key=lambda t: t[1], reverse=True)
        return [HighlightedWord(word=w, weight=round(d, 4)) for w, d in scored[:top_k]]


@lru_cache(maxsize=1)
def get_scam_transformer() -> ScamTransformer:
    """Process-wide singleton (loads the fine-tuned model once)."""
    return ScamTransformer()
