"""Serving-time predictor for the Message Fraud Detector.

Loads the trained pipeline once, scores messages, and produces per-message SHAP
explanations. Explanations use XGBoost's exact TreeSHAP (`pred_contribs=True`),
which is the same algorithm the `shap` library uses for tree models but requires
no extra dependency — so explanations never fail in production.

This module is imported directly by the FastAPI infrastructure layer, guaranteeing
the API applies identical preprocessing and feature logic to what was trained.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import xgboost as xgb

from ..common.features import (
    FEATURE_DESCRIPTIONS,
    FEATURE_NAMES,
    FEATURE_SAFE_DESCRIPTIONS,
)

MODEL_NAME = "message_fraud"


def _default_registry_dir() -> Path:
    env = os.getenv("MODEL_REGISTRY_DIR")
    if env:
        return Path(env)
    # ml/snaija_ml/serving/predictor.py -> ml/models
    return Path(__file__).resolve().parents[2] / "models"


@dataclass
class Contribution:
    feature: str
    label: str          # human-friendly label
    signal: str         # "fraud" | "safe"
    weight: float       # absolute SHAP contribution


@dataclass
class Prediction:
    fraud_probability: float
    is_fraud: bool
    risk_band: str
    risk_label: str
    verdict: str
    contributions: list[Contribution] = field(default_factory=list)
    model_version: str = "unknown"


class ModelNotTrainedError(RuntimeError):
    """Raised when the model registry has no trained artifact yet."""


# Placeholder TF-IDF tokens that carry clear meaning: (fraud-framed, safe-framed).
_PLACEHOLDER_LABELS: dict[str, tuple[str, str]] = {
    "_url_": ("Contains a suspicious link", "No suspicious links"),
    "_phone_": ("Contains a phone number to contact", "No unknown number to contact"),
    "_acctnum_": ("Contains an account number", "No account number quoted"),
    "_longnum_": ("Contains a long numeric code", "No suspicious numeric codes"),
}


def _concept_labels(raw_name: str) -> tuple[str, str] | None:
    """Return (fraud_label, safe_label) for a feature, or None to hide it.

    Engineered features and a few meaningful TF-IDF placeholders are surfaced;
    raw vocabulary terms are hidden to keep explanations clean and trustworthy.
    """
    if raw_name in FEATURE_DESCRIPTIONS:
        return FEATURE_DESCRIPTIONS[raw_name], FEATURE_SAFE_DESCRIPTIONS[raw_name]
    if raw_name.startswith("term::"):
        return _PLACEHOLDER_LABELS.get(raw_name[len("term::"):])
    return None


class MessageFraudPredictor:
    def __init__(self, registry_dir: Path | None = None) -> None:
        self.registry_dir = registry_dir or _default_registry_dir()
        model_dir = self.registry_dir / MODEL_NAME
        model_path = model_dir / "model.joblib"
        if not model_path.exists():
            raise ModelNotTrainedError(
                f"No trained model at {model_path}. Run "
                f"`python -m snaija_ml.pipelines.train_message_fraud` first."
            )
        self._pipeline = joblib.load(model_path)
        self._features = self._pipeline.named_steps["features"]
        self._clf = self._pipeline.named_steps["clf"]
        self._booster = self._clf.get_booster()

        # Optional Platt (sigmoid-on-margin) calibrator maps the raw model score
        # to a trustworthy probability. Absent for older models -> raw probability.
        cal_path = model_dir / "calibrator.joblib"
        self._calibrator = joblib.load(cal_path) if cal_path.exists() else None

        meta_path = model_dir / "metadata.json"
        self.metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        self.version = self.metadata.get("version", "unknown")
        self.threshold = float(self.metadata.get("decision_threshold", 0.5))
        self._risk_bands = self.metadata.get("risk_bands", [])

        names_path = model_dir / "feature_names.json"
        if names_path.exists():
            self._feature_names = json.loads(names_path.read_text(encoding="utf-8"))["names"]
        else:  # fall back to reconstructing from the fitted vectorizer
            tfidf = self._features.transformer_list[0][1]
            self._feature_names = [f"term::{t}" for t in tfidf.get_feature_names_out()] + FEATURE_NAMES

    # ── public API ────────────────────────────────────────────────────────────

    def predict(self, message: str, top_k: int = 5) -> Prediction:
        matrix = self._features.transform([message])
        if self._calibrator is not None:
            # Platt scaling on the raw margin (log-odds) -> smooth probability.
            margin = float(self._clf.predict(matrix, output_margin=True)[0])
            proba = float(self._calibrator.predict_proba([[margin]])[0, 1])
        else:
            proba = float(self._clf.predict_proba(matrix)[:, 1][0])
        band, label = self._resolve_band(proba)
        is_fraud = proba >= self.threshold

        contributions = self._explain(matrix, top_k=top_k)
        verdict = self._verdict(proba, is_fraud, contributions)

        return Prediction(
            fraud_probability=round(proba, 4),
            is_fraud=is_fraud,
            risk_band=band,
            risk_label=label,
            verdict=verdict,
            contributions=contributions,
            model_version=self.version,
        )

    # ── internals ─────────────────────────────────────────────────────────────

    def _explain(self, matrix, top_k: int) -> list[Contribution]:
        """Exact per-feature TreeSHAP contributions for this single message.

        The SHAP magnitude ranks how influential a signal was; whether we phrase
        it as raising or lowering risk is driven by the *sign* of the signal's
        SHAP contribution. So a neutral cue (a naira amount, a link) that the
        model actually read as reassuring is never surfaced as a red flag, and a
        "safe" verdict can never come back with contradictory fraud factors.
        """
        dmatrix = xgb.DMatrix(matrix)
        # shape: (1, n_features + 1); last column is the bias term.
        contribs = self._booster.predict(dmatrix, pred_contribs=True)[0]
        feature_contribs = contribs[:-1]

        dense = np.asarray(matrix.todense()).ravel() if hasattr(matrix, "todense") \
            else np.asarray(matrix).ravel()

        # Aggregate by concept (fraud-framed label as the key) so many raw TF-IDF
        # terms collapse into one line. We track the summed *signed* SHAP
        # contribution (did the concept push toward fraud or toward safe) and its
        # magnitude (how strongly — used only for ranking).
        aggregated: dict[str, dict] = {}
        for idx, (name, contribution) in enumerate(zip(self._feature_names, feature_contribs)):
            if contribution == 0.0:
                continue
            labels = _concept_labels(name)
            if labels is None:
                continue
            present = bool(dense[idx] > 0.0) if idx < len(dense) else False
            # Placeholder TF-IDF terms are only meaningful when actually present.
            if name.startswith("term::") and not present:
                continue
            fraud_label, safe_label = labels
            entry = aggregated.setdefault(
                fraud_label,
                {"feature": name, "fraud_label": fraud_label,
                 "safe_label": safe_label, "influence": 0.0, "signed": 0.0},
            )
            entry["influence"] += abs(float(contribution))
            entry["signed"] += float(contribution)

        ranked = sorted(aggregated.values(), key=lambda e: e["influence"], reverse=True)
        out: list[Contribution] = []
        for entry in ranked[:top_k]:
            # Direction comes from the SIGN of the SHAP contribution, never from
            # mere presence — so a signal the model read as reassuring can't be
            # mislabelled a red flag on a message the model scored safe.
            raises_risk = entry["signed"] > 0.0
            out.append(
                Contribution(
                    feature=entry["feature"],
                    label=entry["fraud_label"] if raises_risk else entry["safe_label"],
                    signal="fraud" if raises_risk else "safe",
                    weight=round(entry["influence"], 4),
                )
            )
        return out

    def _resolve_band(self, proba: float) -> tuple[str, str]:
        for band in self._risk_bands:
            if proba >= band["min"]:
                return band["band"], band["label"]
        return "minimal", "Looks safe"

    @staticmethod
    def _verdict(proba: float, is_fraud: bool, contributions: list[Contribution]) -> str:
        top_reasons = [c.label for c in contributions if c.signal == "fraud"][:2]
        pct = round(proba * 100)
        if not is_fraud:
            return (
                f"This message looks safe ({pct}% fraud risk). Still, never share "
                f"your BVN, OTP or PIN with anyone."
            )
        reason = f" It {top_reasons[0].lower()}" if top_reasons else ""
        also = f" and {top_reasons[1].lower()}" if len(top_reasons) > 1 else ""
        return (
            f"Warning - this looks like fraud ({pct}% risk).{reason}{also}. "
            f"Do not click any links, call any numbers, or share personal details."
        )


@lru_cache(maxsize=1)
def get_predictor() -> MessageFraudPredictor:
    """Process-wide singleton so the model is loaded from disk only once."""
    return MessageFraudPredictor()
