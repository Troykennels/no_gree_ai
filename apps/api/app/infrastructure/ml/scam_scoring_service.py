"""Adapter for Model 1 - Scam Detection (TF-IDF + Logistic Regression).

Wraps the ``snaija_ml`` scam detector behind a small, readiness-aware surface so
the API can serve it without importing the ML library anywhere else. The detector
returns a 3-way label (Safe / Suspicious / Scam), a probability + confidence, the
suspicious words it highlighted, and a plain-English explanation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScamWord:
    word: str
    weight: float


@dataclass
class ScamResult:
    label: str
    scam_probability: float
    confidence: float
    highlighted_words: list[ScamWord]
    explanation: str
    model_version: str


class ScamScoringService:
    def __init__(self, registry_dir: str | None = None) -> None:
        self._registry_dir = registry_dir
        self._detector = None
        self._load_error: str | None = None
        self._try_load()

    def _try_load(self) -> None:
        try:
            from snaija_ml.serving.scam_predictor import ScamDetector

            reg = Path(self._registry_dir) if self._registry_dir else None
            self._detector = ScamDetector(registry_dir=reg)
            self._load_error = None
        except Exception as exc:  # noqa: BLE001 - surfaced via is_ready/health
            self._detector = None
            self._load_error = str(exc)

    @property
    def is_ready(self) -> bool:
        return self._detector is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def model_version(self) -> str:
        return getattr(self._detector, "version", "unknown") if self._detector else "unavailable"

    def detect(self, message: str) -> ScamResult:
        if self._detector is None:
            self._try_load()  # lazy retry in case it was trained after startup
        if self._detector is None:
            raise RuntimeError(self._load_error or "Scam model unavailable")

        p = self._detector.predict(message)
        return ScamResult(
            label=p.label,
            scam_probability=p.scam_probability,
            confidence=p.confidence,
            highlighted_words=[ScamWord(word=h.word, weight=h.weight) for h in p.highlighted_words],
            explanation=p.explanation,
            model_version=p.model_version,
        )
