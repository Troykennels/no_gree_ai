"""Train the Scam Detection model - TF-IDF + Logistic Regression (SecureNaija Model 1).

A deliberately *interpretable* linear text classifier: with a linear model over
TF-IDF features, every prediction decomposes exactly into ``coef * tfidf`` per
token, so we can highlight the precise words that pushed a message toward "scam"
- no post-hoc approximation needed. That transparency is the whole point of the
linear baseline (the optional DistilBERT upgrade trades it for raw accuracy).

Output contract (served by ``serving/scam_predictor.py``):
  * a 3-way label - Safe / Suspicious / Scam - from two calibrated thresholds,
  * the scam probability and a confidence,
  * the highlighted suspicious words (top positive-contribution tokens present),
  * a plain-English human explanation.

Data comes from the same processed corpora as the message-fraud model
(Nigeria fraud SMS + real UCI SMS Spam), so metrics are honest, not templated.

Run:
    python -m snaija_ml.pipelines.train_scam_detection
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from ..common.text import preprocess_for_tfidf
from ..data.training_data import TrainingDataConfig, load_training_frame

MODEL_NAME = "scam_detection"
MODEL_VERSION = "1.0.0"
SEED = 42
BETA = 2.0  # recall-weighted: missing a scam costs more than a false alarm.

REGISTRY_DIR = Path(__file__).resolve().parents[2] / "models"

LABELS = ["Safe", "Suspicious", "Scam"]


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            preprocessor=preprocess_for_tfidf,
            ngram_range=(1, 2),
            min_df=2,
            max_features=8000,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            C=4.0, max_iter=2000, class_weight="balanced", random_state=SEED,
        )),
    ])


def pick_scam_threshold(y_true: np.ndarray, proba: np.ndarray, beta: float) -> float:
    """F-beta-optimal threshold on validation (recall-weighted)."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, proba)
    best_t, best_f = 0.5, -1.0
    for p, r, t in zip(precisions[:-1], recalls[:-1], thresholds):
        if p + r == 0:
            continue
        f = (1 + beta**2) * (p * r) / (beta**2 * p + r)
        if f > best_f:
            best_f, best_t = f, float(t)
    return round(min(max(best_t, 0.30), 0.85), 4)


def main() -> None:
    print("-> Loading scam corpus from processed datasets ...")
    df, info = load_training_frame(TrainingDataConfig())
    src = ", ".join(f"{k}={v}" for k, v in info["sources"].items())
    X = df["text"].tolist()
    y = df["label"].to_numpy()
    print(f"   origin={info['origin']}  sources: {src}")
    print(f"   {len(df):,} messages ({int(y.sum())} scam / {int((1 - y).sum())} legit)")

    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=SEED)
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=SEED)
    print(f"   split -> train={len(X_train)}  val={len(X_val)}  test={len(X_test)}")

    print("-> 5-fold cross-validation (ROC-AUC) ...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_auc = cross_val_score(build_pipeline(), X_train, y_train, cv=cv, scoring="roc_auc")
    print(f"   ROC-AUC {cv_auc.mean():.4f} +/- {cv_auc.std():.4f}")

    print("-> Fitting final Logistic Regression ...")
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    val_proba = pipe.predict_proba(X_val)[:, 1]
    scam_threshold = pick_scam_threshold(y_val, val_proba, BETA)
    # "Suspicious" band opens below the scam line to catch borderline messages
    # (higher recall) without calling them outright scams.
    suspicious_threshold = round(max(scam_threshold * 0.55, 0.20), 4)
    print(f"   thresholds -> suspicious>={suspicious_threshold}  scam>={scam_threshold}")

    # -- Honest evaluation on the untouched test fold -------------------------
    test_proba = pipe.predict_proba(X_test)[:, 1]
    preds = (test_proba >= scam_threshold).astype(int)
    roc = roc_auc_score(y_test, test_proba)
    ap = average_precision_score(y_test, test_proba)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, preds, average="binary", zero_division=0)
    print("\n-- Test-fold evaluation (binary scam vs legit) --------")
    print(classification_report(y_test, preds, target_names=["legit", "scam"], zero_division=0))
    print(f"ROC-AUC {roc:.4f}  PR-AUC {ap:.4f}  P {precision:.3f}  R {recall:.3f}  F1 {f1:.3f}")

    # 3-class distribution on the test fold (informational).
    band = np.where(test_proba >= scam_threshold, 2,
                    np.where(test_proba >= suspicious_threshold, 1, 0))
    dist = {LABELS[i]: int((band == i).sum()) for i in range(3)}
    print(f"3-class spread on test: {dist}")

    # -- Persist --------------------------------------------------------------
    out_dir = REGISTRY_DIR / MODEL_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_dir / "model.joblib")

    metadata = {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "TF-IDF (1-2 gram) + Logistic Regression",
        "labels": LABELS,
        "suspicious_threshold": suspicious_threshold,
        "scam_threshold": scam_threshold,
        "threshold_objective": f"F{BETA:g} (recall-weighted)",
        "cross_validation": {"roc_auc_mean": round(float(cv_auc.mean()), 4),
                             "roc_auc_std": round(float(cv_auc.std()), 4)},
        "metrics": {
            "roc_auc": round(float(roc), 4),
            "pr_auc": round(float(ap), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "test_size": int(len(y_test)),
        },
        "dataset": {"origin": info["origin"], "sources": info["sources"],
                    "n_scam": info["n_fraud"], "n_legit": info["n_legit"]},
        "upgrade_path": "DistilBERT (serving/scam_transformer.py) - optional, needs torch",
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n[OK] model     -> {out_dir / 'model.joblib'}")
    print(f"[OK] model card -> {out_dir / 'metadata.json'}")


if __name__ == "__main__":
    main()
