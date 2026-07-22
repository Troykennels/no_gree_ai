"""Adapter that fulfils the FraudScoringService port using the snaija_ml package.

This is the ONLY place in the API that imports the ML library. Swapping the model
(e.g. to a fine-tuned Transformer) means changing this file alone.
"""

from __future__ import annotations

from pathlib import Path

from app.domain.entities import FraudAssessment, RiskBand, RiskFactor


def _to_risk_band(band: str) -> RiskBand:
    """Map a model band string to the enum, tolerating unknown values.

    Decouples the API from the model card: a future model that emits a band the
    enum doesn't know about degrades to ELEVATED ("be careful") instead of a 500.
    """
    try:
        return RiskBand(band)
    except ValueError:
        return RiskBand.ELEVATED


class MlFraudScoringService:
    def __init__(self, registry_dir: str | None = None) -> None:
        self._registry_dir = registry_dir
        self._predictor = None
        self._load_error: str | None = None
        self._try_load()

    def _try_load(self) -> None:
        try:
            from snaija_ml.serving.predictor import MessageFraudPredictor

            reg = Path(self._registry_dir) if self._registry_dir else None
            self._predictor = MessageFraudPredictor(registry_dir=reg)
            self._load_error = None
        except Exception as exc:  # noqa: BLE001 - surfaced via is_ready/health
            self._predictor = None
            self._load_error = str(exc)

    @property
    def is_ready(self) -> bool:
        return self._predictor is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def model_version(self) -> str:
        return getattr(self._predictor, "version", "unknown") if self._predictor else "unavailable"

    def score_message(self, message: str) -> FraudAssessment:
        if self._predictor is None:
            # Attempt a lazy reload in case the model was trained after startup.
            self._try_load()
        if self._predictor is None:
            raise RuntimeError(self._load_error or "Fraud model unavailable")

        result = self._predictor.predict(message)
        return FraudAssessment(
            fraud_probability=result.fraud_probability,
            is_fraud=result.is_fraud,
            risk_band=_to_risk_band(result.risk_band),
            risk_label=result.risk_label,
            verdict=result.verdict,
            factors=[
                RiskFactor(label=c.label, signal=c.signal, weight=c.weight)
                for c in result.contributions
            ],
            model_version=result.model_version,
        )
