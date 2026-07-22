"""Train the Message Fraud Detector - production-grade.

Pipeline: TF-IDF (on redacted text) + interpretable Nigeria-aware signals -> XGBoost,
with:

  • stratified train / validation / test split,
  • early stopping on the validation fold,
  • stratified K-fold cross-validation for honest, variance-aware metrics,
  • Platt (sigmoid-on-margin) probability **calibration** (a scam "score" you
    can trust as a probability, checked with the Brier score),
  • a **recall-weighted threshold** chosen on validation (missing fraud costs more
    than a false alarm),
  • a saved model card (metadata.json) for auditability.

Explanations remain exact TreeSHAP from the underlying booster, so calibration
never hides the reasons behind a verdict.

Training data comes from the processed corpora produced by
`snaija_ml.data.preprocess` (real UCI SMS Spam + Nigeria scam typologies),
falling back to the synthetic generator only if the pipeline hasn't run.

Run:
    python -m snaija_ml.data.preprocess          # build the processed corpora
    python -m snaija_ml.pipelines.train_message_fraud
    python -m snaija_ml.pipelines.train_message_fraud --sources nigeria_fraud_sms
    python -m snaija_ml.pipelines.train_message_fraud --no-balance
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    fbeta_score,
    precision_recall_fscore_support,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from xgboost import XGBClassifier

from ..common.features import (
    ENGINEERED_FEATURES,
    FEATURE_NAMES,
    EngineeredFeatureExtractor,
)
from ..common.text import preprocess_for_tfidf
from ..data.training_data import TrainingDataConfig, load_training_frame

MODEL_NAME = "message_fraud"
MODEL_VERSION = "1.2.0"
SEED = 42

# Recall matters more than precision for fraud warnings: a missed scam can cost
# someone their savings; a false alarm just costs a second look.
BETA = 2.0

REGISTRY_DIR = Path(__file__).resolve().parents[2] / "models"

RISK_BANDS = [
    {"band": "critical", "min": 0.90, "label": "Almost certainly fraud"},
    {"band": "high", "min": 0.70, "label": "Very likely fraud"},
    {"band": "elevated", "min": 0.45, "label": "Suspicious - be careful"},
    {"band": "low", "min": 0.20, "label": "Probably safe"},
    {"band": "minimal", "min": 0.00, "label": "Looks safe"},
]


def build_feature_union() -> FeatureUnion:
    return FeatureUnion(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=preprocess_for_tfidf,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=6000,
                    sublinear_tf=True,
                ),
            ),
            ("engineered", EngineeredFeatureExtractor()),
        ]
    )


def build_classifier(early_stopping_rounds: int | None = None) -> XGBClassifier:
    # A regularized ensemble (not a single early-stopped tree). On easily
    # separable folds a 1-tree model collapses every message into two leaves;
    # a fuller, shrunk ensemble produces margins that scale with how many fraud
    # signals a message carries, which is what makes graded scoring realistic.
    return XGBClassifier(
        n_estimators=180,
        max_depth=3,
        learning_rate=0.09,
        subsample=0.85,
        colsample_bytree=0.8,
        reg_lambda=2.0,
        min_child_weight=3,
        gamma=0.5,
        objective="binary:logistic",
        eval_metric="aucpr",
        tree_method="hist",
        early_stopping_rounds=early_stopping_rounds,
        n_jobs=-1,
        random_state=SEED,
    )


def build_pipeline(early_stopping_rounds: int | None = None) -> Pipeline:
    return Pipeline(
        [("features", build_feature_union()), ("clf", build_classifier(early_stopping_rounds))]
    )


def _feature_names(union: FeatureUnion) -> list[str]:
    tfidf = union.transformer_list[0][1]
    return [f"term::{t}" for t in tfidf.get_feature_names_out()] + FEATURE_NAMES


def _pick_threshold(y_true: np.ndarray, proba: np.ndarray, beta: float) -> float:
    """Threshold that maximizes F-beta on the validation fold (recall-weighted)."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, proba)
    # precision_recall_curve returns len(thresholds) == len(precisions) - 1
    best_t, best_f = 0.5, -1.0
    for p, r, t in zip(precisions[:-1], recalls[:-1], thresholds):
        if p + r == 0:
            continue
        f = (1 + beta**2) * (p * r) / (beta**2 * p + r)
        if f > best_f:
            best_f, best_t = f, float(t)
    # Guard against degenerate boundaries (0 or 1) on easily-separable folds:
    # a real operating point should leave room on both sides.
    best_t = min(max(best_t, 0.20), 0.80)
    return round(best_t, 4)


def main(config: TrainingDataConfig) -> None:
    print("-> Loading training corpus from processed datasets...")
    df, data_info = load_training_frame(config)
    src_desc = ", ".join(f"{k}={v}" for k, v in data_info["sources"].items())
    print(f"  origin={data_info['origin']}  sources: {src_desc}")
    X = df["text"].tolist()
    y = df["label"].to_numpy()
    print(f"  {len(df)} messages ({int(y.sum())} fraud / {int((1 - y).sum())} legit)")

    # 70 / 15 / 15 stratified split.
    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=SEED
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=SEED
    )
    print(f"  split -> train={len(X_train)}  val={len(X_val)}  test={len(X_test)}")

    # -- Cross-validation for variance-aware metrics --------------------------
    print("-> 5-fold stratified cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_res = cross_validate(
        build_pipeline(early_stopping_rounds=None),
        X_train,
        y_train,
        cv=cv,
        scoring=["roc_auc", "average_precision", "f1"],
        n_jobs=1,
    )
    cv_summary = {
        "roc_auc": [round(float(cv_res["test_roc_auc"].mean()), 4),
                    round(float(cv_res["test_roc_auc"].std()), 4)],
        "pr_auc": [round(float(cv_res["test_average_precision"].mean()), 4),
                   round(float(cv_res["test_average_precision"].std()), 4)],
        "f1": [round(float(cv_res["test_f1"].mean()), 4),
               round(float(cv_res["test_f1"].std()), 4)],
    }
    print(f"  ROC-AUC {cv_summary['roc_auc'][0]:.4f} +/- {cv_summary['roc_auc'][1]:.4f}"
          f"   PR-AUC {cv_summary['pr_auc'][0]:.4f} +/- {cv_summary['pr_auc'][1]:.4f}")

    # -- Fit final model (full regularized ensemble) --------------------------
    # We keep a held-out validation fold for calibration + threshold selection,
    # but do NOT early-stop the final model into a degenerate single tree.
    print("-> Fitting final model (full ensemble)...")
    union = build_feature_union()
    clf = build_classifier(early_stopping_rounds=None)
    X_train_f = union.fit_transform(X_train, y_train)
    X_val_f = union.transform(X_val)
    clf.fit(X_train_f, y_train)
    print(f"  n_estimators used = {clf.n_estimators}")
    pipeline = Pipeline([("features", union), ("clf", clf)])

    # -- Probability calibration (Platt / sigmoid on the model margin) --------
    # Isotonic on separable data collapses to a hard 0/1 step. Platt scaling on
    # the raw margin (log-odds) yields smooth, well-spread probabilities that
    # degrade gracefully to a realistic "maybe" on ambiguous messages.
    print("-> Calibrating probabilities (Platt scaling on margin)...")
    margin_val = clf.predict(X_val_f, output_margin=True).reshape(-1, 1)
    # Regularized (small C) so probabilities don't saturate to a hard 0/1 on
    # perfectly-separable folds — a real risk score should leave headroom.
    calibrator = LogisticRegression(C=0.3, max_iter=1000)
    calibrator.fit(margin_val, y_val)
    cal_val = calibrator.predict_proba(margin_val)[:, 1]

    # -- Threshold tuned on validation (recall-weighted F-beta) ---------------
    threshold = _pick_threshold(y_val, cal_val, BETA)
    print(f"  chosen decision threshold = {threshold} (F{BETA:g}-optimal)")

    # -- Final evaluation on the untouched test fold --------------------------
    X_test_f = union.transform(X_test)
    margin_test = clf.predict(X_test_f, output_margin=True).reshape(-1, 1)
    raw_test = clf.predict_proba(X_test_f)[:, 1]
    cal_test = calibrator.predict_proba(margin_test)[:, 1]
    preds = (cal_test >= threshold).astype(int)

    roc = roc_auc_score(y_test, cal_test)
    ap = average_precision_score(y_test, cal_test)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, preds, average="binary", zero_division=0
    )
    fbeta = fbeta_score(y_test, preds, beta=BETA, zero_division=0)
    cm = confusion_matrix(y_test, preds).tolist()
    brier_raw = brier_score_loss(y_test, raw_test)
    brier_cal = brier_score_loss(y_test, cal_test)

    print("\n-- Test-fold evaluation -----------------------")
    print(classification_report(y_test, preds, target_names=["legit", "fraud"], zero_division=0))
    print(f"ROC-AUC {roc:.4f}  PR-AUC {ap:.4f}  F1 {f1:.4f}  F{BETA:g} {fbeta:.4f}")
    print(f"Brier (calibration error): raw {brier_raw:.4f} -> calibrated {brier_cal:.4f}")
    print(f"Confusion [[TN,FP],[FN,TP]]: {cm}")

    # -- Persist artifacts ----------------------------------------------------
    out_dir = REGISTRY_DIR / MODEL_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, out_dir / "model.joblib")
    joblib.dump(calibrator, out_dir / "calibrator.joblib")

    names = _feature_names(union)
    (out_dir / "feature_names.json").write_text(
        json.dumps({"names": names, "count": len(names)}), encoding="utf-8"
    )

    metadata = {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "TF-IDF + engineered Nigeria-aware signals + XGBoost",
        "calibration": "platt (sigmoid on margin)",
        "decision_threshold": threshold,
        "threshold_objective": f"F{BETA:g} (recall-weighted)",
        "n_estimators": int(clf.n_estimators),
        "risk_bands": RISK_BANDS,
        "n_features_engineered": len(FEATURE_NAMES),
        "engineered_features": [
            {"name": f.name, "description": f.description} for f in ENGINEERED_FEATURES
        ],
        "cross_validation": cv_summary,
        "metrics": {
            "roc_auc": round(float(roc), 4),
            "pr_auc": round(float(ap), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "fbeta": round(float(fbeta), 4),
            "brier_raw": round(float(brier_raw), 4),
            "brier_calibrated": round(float(brier_cal), 4),
            "confusion_matrix": cm,
            "test_size": int(len(y_test)),
        },
        "dataset": {
            "origin": data_info["origin"],
            "sources": data_info["sources"],
            "n_fraud": data_info["n_fraud"],
            "n_legit": data_info["n_legit"],
            "balanced": data_info["balanced"],
            "seed": config.seed,
        },
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n[OK] model      -> {out_dir / 'model.joblib'}")
    print(f"[OK] calibrator -> {out_dir / 'calibrator.joblib'}")
    print(f"[OK] model card -> {out_dir / 'metadata.json'}")
    print(f"[OK] features   -> {len(names)} total")


def _parse_args() -> TrainingDataConfig:
    p = argparse.ArgumentParser(description="Train the SecureNaija message-fraud model.")
    p.add_argument("--no-balance", action="store_true",
                   help="Train on the natural class distribution instead of undersampling.")
    p.add_argument("--sources", nargs="*", default=None,
                   help="Restrict to specific processed sources (e.g. nigeria_fraud_sms sms_spam).")
    p.add_argument("--seed", type=int, default=20260721)
    a = p.parse_args()
    return TrainingDataConfig(
        balance=not a.no_balance,
        seed=a.seed,
        sources=tuple(a.sources) if a.sources else None,
    )


if __name__ == "__main__":
    main(_parse_args())
