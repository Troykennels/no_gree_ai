"""Serve the Scam Detection model (TF-IDF + Logistic Regression, Model 1).

Because the model is linear over TF-IDF features, an exact per-word explanation
is just ``coef * tfidf_value`` - no SHAP approximation. We surface:

  * label   - Safe / Suspicious / Scam (two thresholds from the model card),
  * probability + confidence,
  * highlighted_words - the tokens that most pushed the message toward "scam",
  * explanation - a plain-English sentence a non-technical user can act on.

Train/serve parity is guaranteed: we load the exact pickled pipeline and reuse
the shared ``preprocess_for_tfidf`` (baked into the vectorizer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

REGISTRY_DIR = Path(__file__).resolve().parents[2] / "models"

# Friendly names for the redaction placeholders so a user sees a concept, not a token.
_PLACEHOLDER_LABELS = {
    "_url_": "a suspicious link",
    "_phone_": "a phone number to call",
    "_longnum_": "a long code / number",
    "_acctnum_": "an account-like number",
}


@dataclass
class HighlightedWord:
    word: str
    weight: float


@dataclass
class ScamPrediction:
    label: str                     # Safe | Suspicious | Scam
    scam_probability: float        # 0..1
    confidence: float              # 0..1, how sure the model is of the direction
    highlighted_words: list[HighlightedWord] = field(default_factory=list)
    explanation: str = ""
    model_version: str = "unknown"


class ScamDetector:
    def __init__(self, registry_dir: Path | None = None) -> None:
        import json

        model_dir = (registry_dir or REGISTRY_DIR) / "scam_detection"
        self._pipe = joblib.load(model_dir / "model.joblib")
        meta = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
        self.version = meta["version"]
        self.labels = meta["labels"]
        self._t_susp = float(meta["suspicious_threshold"])
        self._t_scam = float(meta["scam_threshold"])

        self._vec = self._pipe.named_steps["tfidf"]
        self._clf = self._pipe.named_steps["clf"]
        self._coef = self._clf.coef_[0]
        self._feature_names = self._vec.get_feature_names_out()

    def predict(self, message: str, top_k: int = 6) -> ScamPrediction:
        proba = float(self._pipe.predict_proba([message])[0, 1])

        if proba >= self._t_scam:
            label = "Scam"
        elif proba >= self._t_susp:
            label = "Suspicious"
        else:
            label = "Safe"

        confidence = round(max(proba, 1.0 - proba), 4)
        highlights = self._highlight(message, top_k)
        explanation = self._explain(label, proba, highlights)

        return ScamPrediction(
            label=label,
            scam_probability=round(proba, 4),
            confidence=confidence,
            highlighted_words=highlights,
            explanation=explanation,
            model_version=self.version,
        )

    # ── internals ──────────────────────────────────────────────────────────
    def _highlight(self, message: str, top_k: int) -> list[HighlightedWord]:
        """Exact linear contributions: coef * tfidf. Positive => pushes to scam."""
        x = self._vec.transform([message])
        x = x.tocoo()
        scored: list[tuple[str, float]] = []
        for idx, val in zip(x.col, x.data):
            contribution = float(self._coef[idx]) * float(val)
            if contribution <= 0:
                continue
            token = self._feature_names[idx]
            word = _PLACEHOLDER_LABELS.get(token, token)
            scored.append((word, contribution))

        scored.sort(key=lambda t: t[1], reverse=True)
        # Deduplicate friendly labels while keeping the strongest weight.
        seen: dict[str, float] = {}
        for word, w in scored:
            if word not in seen:
                seen[word] = w
            if len(seen) >= top_k:
                break
        return [HighlightedWord(word=w, weight=round(val, 4)) for w, val in seen.items()]

    def _explain(self, label: str, proba: float, highlights: list[HighlightedWord]) -> str:
        pct = round(proba * 100)
        words = ", ".join(f'"{h.word}"' for h in highlights[:3])
        if label == "Scam":
            tail = f" Watch out for {words}." if words else ""
            return (f"Scam ({pct}% risk).{tail} Do not click links, call numbers, "
                    f"or share your BVN, OTP or PIN.")
        if label == "Suspicious":
            tail = f" It contains {words}." if words else ""
            return (f"Suspicious ({pct}% risk) - treat with caution.{tail} "
                    f"Verify the sender through an official channel before acting.")
        return (f"Looks safe ({pct}% risk). Still, never share your BVN, OTP or "
                f"PIN with anyone.")


@lru_cache(maxsize=1)
def get_scam_detector() -> ScamDetector:
    """Process-wide singleton so the model loads from disk only once."""
    return ScamDetector()
