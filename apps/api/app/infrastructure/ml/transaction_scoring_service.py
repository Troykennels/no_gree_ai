"""Adapter for Model 2 - Transaction Fraud (XGBoost / RandomForest on IEEE-CIS).

Wraps the ``snaija_ml`` transaction predictor. Callers send a flexible dict of the
transaction fields they know; every expected column that is missing is imputed
exactly as during training. Returns a fraud probability, an approve/review/decline
decision, a risk band, and the per-transaction TreeSHAP factors that drove it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# No Gree AI is a Nigerian product: callers send amounts in Naira (NGN). The
# Model 2 corpus (IEEE-CIS) is denominated in a smaller unit, so we scale NGN to
# the model's training magnitude only for scoring - the Naira value is preserved
# for display. Cosmetic demo rate; a real deployment would use a live FX feed.
NGN_PER_MODEL_UNIT = 1650.0


@dataclass
class TxnFactorOut:
    feature: str
    label: str
    signal: str
    weight: float


@dataclass
class TransactionResult:
    fraud_probability: float
    confidence: float
    is_fraud: bool
    decision: str
    risk_band: str
    reasons: list[str]
    verdict: str
    risk_explanation: str
    factors: list[TxnFactorOut]
    model_version: str
    algorithm: str


class TransactionScoringService:
    def __init__(self, registry_dir: str | None = None) -> None:
        self._registry_dir = registry_dir
        self._predictor = None
        self._load_error: str | None = None
        self._try_load()

    def _try_load(self) -> None:
        try:
            from snaija_ml.serving.transaction_predictor import TransactionFraudPredictor

            reg = Path(self._registry_dir) if self._registry_dir else None
            self._predictor = TransactionFraudPredictor(registry_dir=reg)
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

    @property
    def algorithm(self) -> str:
        return getattr(self._predictor, "algorithm", "unknown") if self._predictor else "unavailable"

    @property
    def expected_fields(self) -> dict[str, list[str]]:
        return self._predictor.expected_fields if self._predictor else {"numeric": [], "categorical": []}

    @staticmethod
    def _input_risk(features: dict) -> tuple[float, list[str]]:
        """Transparent rule-based risk over the fields a user actually supplies (in
        Naira). Passed to the model as a risk floor so obviously risky inputs - very
        large amounts, high account activity - are flagged even though the full
        IEEE-CIS feature set is not available at manual entry time."""
        risk = 0.0
        reasons: list[str] = []
        amt = features.get("TransactionAmt")
        if amt is not None:
            try:
                ngn = float(amt)
                if ngn >= 2_000_000:
                    risk = max(risk, 0.85)
                elif ngn >= 1_000_000:
                    risk = max(risk, 0.62)
                elif ngn >= 500_000:
                    risk = max(risk, 0.42)
                elif ngn >= 150_000:
                    risk = max(risk, 0.22)
                if ngn >= 500_000:
                    reasons.append("Large or unusual amount")
            except (TypeError, ValueError):
                pass
        activity = 0.0
        for c in ("C1", "C13", "C14", "C2"):
            v = features.get(c)
            if v is None:
                continue
            try:
                n = float(v)
                if n >= 40:
                    activity = max(activity, 0.70)
                elif n >= 20:
                    activity = max(activity, 0.50)
                elif n >= 10:
                    activity = max(activity, 0.30)
            except (TypeError, ValueError):
                pass
        if activity > 0:
            risk = max(risk, activity)
            if activity >= 0.50:
                reasons.append("Unusual account activity")
        if str(features.get("card6", "")).lower() == "credit":
            risk = min(0.97, risk + 0.04)
        if str(features.get("ProductCD", "")).upper() in {"C", "S"}:
            risk = min(0.97, risk + 0.04)
        return min(risk, 0.97), reasons

    def score(self, features: dict) -> TransactionResult:
        if self._predictor is None:
            self._try_load()  # lazy retry in case it was trained after startup
        if self._predictor is None:
            raise RuntimeError(self._load_error or "Transaction model unavailable")

        # Scale the Naira amount into the model's training magnitude (copy so the
        # caller's Naira value is untouched for storage/display).
        feats = dict(features)
        amt = feats.get("TransactionAmt")
        if amt is not None:
            try:
                feats["TransactionAmt"] = float(amt) / NGN_PER_MODEL_UNIT
            except (TypeError, ValueError):
                pass
        # Rule-based risk floor over the raw (Naira) fields the caller supplied, so
        # the tool responds to obviously risky inputs (see _input_risk).
        floor, floor_reasons = self._input_risk(features)
        p = self._predictor.predict(feats, risk_floor=floor, floor_reasons=floor_reasons)
        return TransactionResult(
            fraud_probability=p.fraud_probability,
            confidence=p.confidence,
            is_fraud=p.is_fraud,
            decision=p.decision,
            risk_band=p.risk_band,
            reasons=list(p.reasons),
            verdict=p.verdict,
            risk_explanation=p.risk_explanation,
            factors=[TxnFactorOut(feature=f.feature, label=f.label, signal=f.signal, weight=f.weight)
                     for f in p.factors],
            model_version=p.model_version,
            algorithm=p.algorithm,
        )
