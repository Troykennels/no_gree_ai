"""Serving-time predictor for the Transaction Fraud Detector (Model 2).

Loads the trained pipeline (shared preprocessor + best tree model) once and scores
a single card transaction supplied as a flexible ``{feature: value}`` dict. The
caller only has to send the fields it knows about - every expected column that is
missing is imputed exactly as it was during training (the preprocessor is baked
into the pickle), so there is zero train/serve skew.

Explanations use XGBoost's exact per-instance TreeSHAP (``pred_contribs=True``) -
the same algorithm the ``shap`` library uses for trees, but with no extra
dependency, so explanations never fail in production. Each factor's *sign* says
whether it pushed the transaction toward fraud or toward legitimate.

Imported directly by the FastAPI infrastructure layer, guaranteeing identical
preprocessing to training.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_NAME = "transaction_fraud"


def _default_registry_dir() -> Path:
    env = os.getenv("MODEL_REGISTRY_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "models"


# Plain-English *reasons* for each IEEE-CIS feature block, in both directions:
# (phrase when the signal RAISES risk, phrase when it LOWERS risk). A
# non-technical user reads "Large transaction", never "V70" or "C13".
def _reason(name: str, raises: bool) -> str:
    def pick(hi: str, lo: str) -> str:
        return hi if raises else lo

    if name == "TransactionAmt":
        return pick("Large or unusual amount", "Normal transaction amount")
    if name in ("addr1", "addr2"):
        return pick("Unusual billing location", "Familiar billing location")
    if name in ("dist1", "dist2"):
        return pick("Far from the usual location", "Close to the usual location")
    if name == "card4":
        return pick("Uncommon card network", "Common card network")
    if name == "card6":
        return pick("Higher-risk card type", "Lower-risk card type")
    if name.startswith("card"):
        return pick("Unusual card details", "Recognised card")
    if name in ("P_emaildomain", "R_emaildomain"):
        return pick("Suspicious email domain", "Trusted email domain")
    if name == "ProductCD":
        return pick("Higher-risk product type", "Everyday product type")
    if name in ("DeviceType", "DeviceInfo"):
        return pick("Unknown or new device", "Known device")
    if name.startswith("C") and name[1:].isdigit():
        return pick("Unusual account activity", "Normal account activity")
    if name.startswith("D") and name[1:].isdigit():
        return pick("Unusual account timing", "Consistent account timing")
    if name.startswith("M") and name[1:].isdigit():
        return pick("Identity details don't match", "Identity details match")
    if name.startswith("V") and name[1:].isdigit():
        return pick("Matches known fraud patterns", "No known fraud pattern")
    return name


@dataclass
class TxnFactor:
    feature: str
    label: str
    signal: str        # "fraud" | "safe"
    weight: float      # absolute SHAP contribution (ranking magnitude)


@dataclass
class TransactionPrediction:
    fraud_probability: float
    confidence: float             # 0..1, how sure the model is of its call
    is_fraud: bool
    decision: str                 # "approve" | "review" | "decline"
    risk_band: str                # minimal | low | elevated | high | critical
    reasons: list[str] = field(default_factory=list)   # plain red-flag phrases
    factors: list[TxnFactor] = field(default_factory=list)
    verdict: str = ""             # plain human explanation
    risk_explanation: str = ""    # what the risk means + what could happen
    model_version: str = "unknown"
    algorithm: str = "unknown"


class TransactionModelNotTrainedError(RuntimeError):
    """Raised when the transaction-fraud model has not been trained yet."""


_BANDS = [  # (min_probability, band, label)
    (0.90, "critical", "Almost certainly fraud"),
    (0.70, "high", "High fraud risk"),
    (0.40, "elevated", "Elevated fraud risk"),
    (0.15, "low", "Low fraud risk"),
    (0.00, "minimal", "Looks legitimate"),
]


class TransactionFraudPredictor:
    def __init__(self, registry_dir: Path | None = None) -> None:
        self.registry_dir = registry_dir or _default_registry_dir()
        model_dir = self.registry_dir / MODEL_NAME
        model_path = model_dir / "model.joblib"
        if not model_path.exists():
            raise TransactionModelNotTrainedError(
                f"No trained model at {model_path}. Run "
                f"`python -m snaija_ml.pipelines.train_transaction_fraud` first."
            )
        self._pipeline = joblib.load(model_path)
        self._pre = self._pipeline.named_steps["preprocess"]
        self._clf = self._pipeline.named_steps["clf"]

        meta_path = model_dir / "metadata.json"
        self.metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        self.version = self.metadata.get("version", "unknown")
        self.algorithm = self.metadata.get("algorithm", "unknown")
        self.threshold = float(self.metadata.get("decision_threshold", 0.5))

        # Recover the raw input columns the preprocessor expects (order matters).
        self._num_cols: list[str] = []
        self._cat_cols: list[str] = []
        for name, _trans, cols in self._pre.transformers_:
            if name == "num":
                self._num_cols = list(cols)
            elif name == "cat":
                self._cat_cols = list(cols)
        self._input_cols = self._num_cols + self._cat_cols

        names_path = model_dir / "feature_names.json"
        if names_path.exists():
            self._feature_names = json.loads(names_path.read_text(encoding="utf-8"))["names"]
        else:
            self._feature_names = list(self._pre.get_feature_names_out())

        # Native TreeSHAP is only available for the XGBoost booster.
        self._booster = self._clf.get_booster() if hasattr(self._clf, "get_booster") else None

    @property
    def expected_fields(self) -> dict[str, list[str]]:
        """The feature names callers may supply (all optional; missing = imputed)."""
        return {"numeric": self._num_cols, "categorical": self._cat_cols}

    # ── public API ─────────────────────────────────────────────────────────────

    def predict(self, features: dict, top_k: int = 6) -> TransactionPrediction:
        row: dict[str, object] = {c: features.get(c, np.nan) for c in self._num_cols}
        row.update({c: features.get(c, None) for c in self._cat_cols})
        frame = pd.DataFrame([row], columns=self._input_cols)

        proba = float(self._pipeline.predict_proba(frame)[0, 1])
        confidence = round(max(proba, 1.0 - proba), 4)
        is_fraud = proba >= self.threshold
        decision = ("decline" if proba >= self.threshold
                    else "review" if proba >= self.threshold * 0.5 else "approve")
        band, band_label = self._resolve_band(proba)
        factors = self._explain(frame, top_k)
        reasons = [f.label for f in factors if f.signal == "fraud"]
        verdict = self._verdict(proba, decision, band_label, reasons)
        risk_explanation = self._risk_explanation(decision, proba)

        return TransactionPrediction(
            fraud_probability=round(proba, 4),
            confidence=confidence,
            is_fraud=is_fraud,
            decision=decision,
            risk_band=band,
            reasons=reasons,
            factors=factors,
            verdict=verdict,
            risk_explanation=risk_explanation,
            model_version=self.version,
            algorithm=self.algorithm,
        )

    # ── internals ──────────────────────────────────────────────────────────────

    def _explain(self, frame: pd.DataFrame, top_k: int) -> list[TxnFactor]:
        """Per-instance TreeSHAP (XGBoost). Sign => raises vs lowers fraud risk."""
        if self._booster is None:
            return []
        import xgboost as xgb

        X = self._pre.transform(frame).astype("float32")
        contribs = self._booster.predict(xgb.DMatrix(X), pred_contribs=True)[0]
        feature_contribs = contribs[:-1]  # drop bias

        order = np.argsort(np.abs(feature_contribs))[::-1][:top_k]
        out: list[TxnFactor] = []
        for idx in order:
            c = float(feature_contribs[idx])
            if c == 0.0:
                continue
            name = self._feature_names[idx] if idx < len(self._feature_names) else str(idx)
            out.append(TxnFactor(
                feature=name,
                label=_reason(name, raises=c > 0),
                signal="fraud" if c > 0 else "safe",
                weight=round(abs(c), 4),
            ))
        return out

    @staticmethod
    def _resolve_band(proba: float) -> tuple[str, str]:
        for min_p, band, label in _BANDS:
            if proba >= min_p:
                return band, label
        return "minimal", "Looks legitimate"

    @staticmethod
    def _verdict(proba: float, decision: str, band_label: str,
                 reasons: list[str]) -> str:
        pct = round(proba * 100)
        drivers = [r.lower() for r in reasons][:2]
        because = f" Mainly because of {', '.join(drivers)}." if drivers else ""
        if decision == "decline":
            return (f"This transaction looks fraudulent ({pct}% risk).{because} "
                    f"Block the card and confirm with the customer before it goes through.")
        if decision == "review":
            return (f"This transaction is worth a second look ({pct}% risk).{because} "
                    f"Ask for an OTP or call the customer before approving.")
        return f"This transaction looks normal ({pct}% fraud risk). Safe to approve."

    @staticmethod
    def _risk_explanation(decision: str, proba: float) -> str:
        pct = round(proba * 100)
        if decision == "decline":
            return (f"High fraud risk ({pct}%). If this payment goes through, the "
                    f"cardholder could lose money that is hard to recover.")
        if decision == "review":
            return (f"Medium fraud risk ({pct}%). It may be genuine, but a quick check "
                    f"now avoids a costly mistake later.")
        return (f"Low fraud risk ({pct}%). This looks like normal spending - just keep "
                f"an eye on your statement.")


@lru_cache(maxsize=1)
def get_transaction_predictor() -> TransactionFraudPredictor:
    """Process-wide singleton so the model is loaded from disk only once."""
    return TransactionFraudPredictor()
