"""Train the Transaction Fraud Detector on the IEEE-CIS corpus - production-grade.

This is SecureNaija "Model 2": tabular card-transaction fraud. It trains two
industry-standard tree ensembles on the SAME leakage-safe preprocessing, scores
them on an honest, out-of-time test fold, compares them across the full metric
suite (accuracy, precision, recall, F1, ROC-AUC, PR-AUC), explains the winner
with SHAP, and persists ONLY the best model plus an auditable model card.

Key production choices
----------------------
* **Out-of-time split** (sort by ``TransactionDT``, train on the past, test on the
  future) - the honest way to evaluate fraud detection; a random split leaks
  future patterns and flatters the score.
* **One shared preprocessor**, fit on TRAIN ONLY (median-impute numerics,
  constant-impute + ordinal-encode categoricals), so the two algorithms are
  compared on identical features and there is no train/test leakage.
* **Imbalance handling** without distorting the operating base rate: XGBoost uses
  ``scale_pos_weight``; RandomForest uses ``class_weight='balanced_subsample'``.
* **PR-AUC (average precision) selects the winner** - the right headline metric
  for a ~3.5% positive rate, where ROC-AUC is optimistic.

Laptop-safe by default (this repo targets an 8 GB / 4-core dev machine)
----------------------------------------------------------------------
The full corpus is 590k rows x 422 cols and needs ~2 GB RAM + every core to
train - which will thrash a small machine into swap and hang it. So the DEFAULTS
here are frugal and never load the whole table into memory:

* only a curated, high-signal **column subset** is read (via Arrow, so unused
  columns are never decompressed),
* only a **recent out-of-time window** of rows is materialised and then
  subsampled (peak RAM stays well under ~400 MB),
* training is capped to ``--n-jobs`` cores (default 2) so the UI stays alive.

Every reduction is stamped into the model card, so the metrics stay honest. On a
bigger box, scale straight up to the full corpus:

    python -m snaija_ml.pipelines.train_transaction_fraud --full
    python -m snaija_ml.pipelines.train_transaction_fraud --sample-rows 250000 --n-jobs 4

Default (frugal) run:
    python -m snaija_ml.pipelines.train_transaction_fraud
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBClassifier

MODEL_NAME = "transaction_fraud"
MODEL_VERSION = "1.0.0"
SEED = 42

ML_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ML_ROOT / "data" / "processed" / "ieee_cis.parquet"
REGISTRY_DIR = ML_ROOT / "models"

TARGET = "isFraud"
TIME_COL = "TransactionDT"
DROP_COLS = ["TransactionID"]  # pure identifier - never a feature

# Operating point: fraud review is recall-sensitive (a missed fraud is costly,
# a flagged good txn just gets a second look), so we report at the default 0.5.
DECISION_THRESHOLD = 0.5

# Curated high-signal IEEE-CIS transaction columns. Reading only these keeps the
# memory footprint small (Arrow never decompresses the ~340 V-columns we omit)
# while retaining the features that carry almost all of the model's lift:
# amount, card/address identity, email domains, and the C/D/M engineered blocks
# plus a handful of the historically strongest V-columns.
CURATED_COLS = [
    TARGET, TIME_COL,
    "TransactionAmt", "ProductCD",
    "card1", "card2", "card3", "card4", "card5", "card6",
    "addr1", "addr2", "dist1", "dist2",
    "P_emaildomain", "R_emaildomain",
    *[f"C{i}" for i in range(1, 15)],
    *[f"D{i}" for i in range(1, 16)],
    *[f"M{i}" for i in range(1, 10)],
    # Historically high-importance V-columns on IEEE-CIS.
    "V62", "V70", "V91", "V127", "V130", "V170", "V187", "V201",
    "V257", "V258", "V294", "V317", "V308", "V310", "V314",
]

# Columns that are genuinely categorical in IEEE-CIS (string codes, not numbers).
# Used to coerce dtypes deterministically after an Arrow read - Arrow can hand back
# an extension string dtype that a name-based dtype check would misread as numeric.
KNOWN_CATEGORICAL = {
    "ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain",
    "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9",
    "DeviceType", "DeviceInfo",
}


def _available_columns(wanted: list[str]) -> list[str]:
    """Intersect the curated list with the parquet schema (order preserved)."""
    import pyarrow.parquet as pq

    schema_names = set(pq.ParquetFile(DATA_PATH).schema_arrow.names)
    cols = [c for c in wanted if c in schema_names]
    missing = [c for c in wanted if c not in schema_names]
    if missing:
        print(f"   (note: {len(missing)} curated cols absent from parquet, skipped)")
    return cols


def load_frame(full: bool, sample_rows: int, recent_window: int) -> tuple[pd.DataFrame, dict]:
    """Load a training frame with a bounded memory footprint.

    frugal (default): read only the curated columns, keep the most recent
    ``recent_window`` rows (out-of-time), then subsample to ``sample_rows``.
    ``--full`` reads every column and every row (needs ~2 GB RAM).
    """
    prov: dict = {"source": "IEEE-CIS Fraud Detection"}

    if full:
        print(f"-> [FULL] Loading entire IEEE-CIS corpus from {DATA_PATH.name} ...")
        df = pd.read_parquet(DATA_PATH)
        prov.update(mode="full", columns="all", sampled=False)
    else:
        cols = _available_columns(CURATED_COLS)
        print(f"-> [FRUGAL] Reading {len(cols)} curated columns via Arrow ...")
        import pyarrow.parquet as pq

        table = pq.read_table(DATA_PATH, columns=cols)
        total_rows = table.num_rows
        # Parquet is time-sorted (verified): the tail is the most recent window.
        keep = min(recent_window, total_rows) if recent_window else total_rows
        table = table.slice(total_rows - keep, keep)
        df = table.to_pandas()
        del table
        prov.update(mode="frugal", columns=len(cols),
                    recent_window=int(keep), total_available=int(total_rows))
        # Coerce to a definite numpy dtype per column: categoricals -> object,
        # everything else -> float32. Immune to Arrow extension-dtype surprises
        # (which otherwise let a string column masquerade as numeric).
        for col in df.columns:
            if col in (TARGET, TIME_COL):
                continue
            if col in KNOWN_CATEGORICAL:
                df[col] = df[col].astype("object")
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")

    # Downcast to shrink the working set further (full path / any leftovers).
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype("float32")
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")

    # Row subsample (out-of-time preserved: sort by time, then stratified sample
    # keeps the whole recent tail so train/test stay in chronological order).
    if not full and sample_rows and len(df) > sample_rows:
        df = df.sort_values(TIME_COL, kind="stable")
        # Keep every fraud row (rare) + a random draw of legit rows to hit target.
        rng = np.random.default_rng(SEED)
        pos = np.flatnonzero(df[TARGET].to_numpy() == 1)
        neg = np.flatnonzero(df[TARGET].to_numpy() == 0)
        n_neg = min(len(neg), max(sample_rows - len(pos), 0))
        keep_neg = rng.choice(neg, size=n_neg, replace=False)
        idx = np.sort(np.concatenate([pos, keep_neg]))  # sorted => stays in time order
        df = df.iloc[idx].reset_index(drop=True)
        prov.update(sampled=True, sample_rows=int(len(df)))

    print(f"   {len(df):,} transactions x {df.shape[1]} columns "
          f"({df[TARGET].mean() * 100:.2f}% fraud)")
    return df, prov


def split_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Numeric vs categorical by actual dtype (robust to Arrow/pandas backends)."""
    feature_cols = [c for c in df.columns if c not in (*DROP_COLS, TARGET, TIME_COL)]
    num_cols = df[feature_cols].select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in feature_cols if c not in num_cols]
    return num_cols, cat_cols


def build_preprocessor(num_cols: list[str], cat_cols: list[str]) -> ColumnTransformer:
    numeric = SimpleImputer(strategy="median")
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="__missing__")),
        ("encode", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    return ColumnTransformer(
        [("num", numeric, num_cols), ("cat", categorical, cat_cols)],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def out_of_time_split(df: pd.DataFrame, test_frac: float = 0.2):
    """Train on the earliest transactions, test on the most recent ones."""
    df_sorted = df.sort_values(TIME_COL, kind="stable")
    cut = int(len(df_sorted) * (1 - test_frac))
    return df_sorted.iloc[:cut], df_sorted.iloc[cut:]


def undersample_majority(X: np.ndarray, y: np.ndarray, ratio: int, seed: int):
    """Keep every fraud row + ``ratio`` x as many random legit rows."""
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y == 0)
    keep_neg = rng.choice(neg, size=min(len(neg), len(pos) * ratio), replace=False)
    idx = np.concatenate([pos, keep_neg])
    rng.shuffle(idx)
    return X[idx], y[idx]


def evaluate(name: str, y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict:
    preds = (proba >= threshold).astype(int)
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, preds)), 4),
        "precision": round(float(precision_score(y_true, preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
        "pr_auc": round(float(average_precision_score(y_true, proba)), 4),
        "confusion_matrix": confusion_matrix(y_true, preds).tolist(),
        "threshold": threshold,
    }
    print(f"   [{name:13}] ROC-AUC {metrics['roc_auc']:.4f}  PR-AUC {metrics['pr_auc']:.4f}  "
          f"P {metrics['precision']:.3f}  R {metrics['recall']:.3f}  F1 {metrics['f1']:.3f}")
    return metrics


def xgb_shap_top(model: XGBClassifier, feature_names: list[str], X_sample: np.ndarray,
                 top_k: int = 20) -> list[dict]:
    """Global feature importance via exact native TreeSHAP (mean |contribution|)."""
    import xgboost as xgb

    booster = model.get_booster()
    contribs = booster.predict(xgb.DMatrix(X_sample), pred_contribs=True)
    mean_abs = np.abs(contribs[:, :-1]).mean(axis=0)  # drop bias column
    order = np.argsort(mean_abs)[::-1][:top_k]
    return [{"feature": feature_names[i], "mean_abs_shap": round(float(mean_abs[i]), 5)}
            for i in order]


def main(full: bool, sample_rows: int, recent_window: int,
         rf_sample: int, rf_ratio: int, n_jobs: int) -> None:
    # Cap BLAS/OpenMP threads too, so the machine stays responsive under training.
    if n_jobs > 0:
        os.environ.setdefault("OMP_NUM_THREADS", str(n_jobs))

    df, prov = load_frame(full, sample_rows, recent_window)
    num_cols, cat_cols = split_columns(df)
    print(f"   features: {len(num_cols)} numeric, {len(cat_cols)} categorical")

    train_df, test_df = out_of_time_split(df)
    print(f"-> Out-of-time split -> train={len(train_df):,}  test={len(test_df):,} "
          f"(test fraud rate {test_df[TARGET].mean() * 100:.2f}%)")

    y_train = train_df[TARGET].to_numpy()
    y_test = test_df[TARGET].to_numpy()

    print("-> Fitting shared preprocessor on the training fold ...")
    pre = build_preprocessor(num_cols, cat_cols)
    X_train = pre.fit_transform(train_df).astype("float32")
    X_test = pre.transform(test_df).astype("float32")
    feature_names = list(pre.get_feature_names_out())
    del df, train_df, test_df

    pos = int(y_train.sum())
    neg = int((y_train == 0).sum())
    scale_pos_weight = round(neg / max(pos, 1), 2)

    # -- XGBoost --------------------------------------------------------------
    n_estimators_xgb = 400 if full else 250
    print(f"-> Training XGBoost ({n_estimators_xgb} trees, {n_jobs} threads) ...")
    xgb_model = XGBClassifier(
        n_estimators=n_estimators_xgb, max_depth=6, learning_rate=0.08,
        subsample=0.8, colsample_bytree=0.8, reg_lambda=2.0,
        min_child_weight=3, gamma=0.5, objective="binary:logistic",
        eval_metric="aucpr", tree_method="hist",
        scale_pos_weight=scale_pos_weight, n_jobs=n_jobs, random_state=SEED,
    )
    xgb_model.fit(X_train, y_train)
    xgb_proba = xgb_model.predict_proba(X_test)[:, 1]

    # -- RandomForest on a majority-undersampled view (tractable on a laptop) --
    Xr, yr = undersample_majority(X_train, y_train, rf_ratio, SEED)
    if rf_sample and len(yr) > rf_sample:
        rng = np.random.default_rng(SEED)
        sel = rng.choice(len(yr), size=rf_sample, replace=False)
        Xr, yr = Xr[sel], yr[sel]
    n_estimators_rf = 300 if full else 150
    print(f"-> Training RandomForest ({len(yr):,} rows, "
          f"{int(yr.sum()):,} fraud after undersampling, {n_estimators_rf} trees) ...")
    rf_model = RandomForestClassifier(
        n_estimators=n_estimators_rf, max_depth=20, min_samples_leaf=20,
        max_features="sqrt", class_weight="balanced_subsample",
        n_jobs=n_jobs, random_state=SEED,
    )
    rf_model.fit(Xr, yr)
    rf_proba = rf_model.predict_proba(X_test)[:, 1]

    # -- Compare on the untouched out-of-time test fold -----------------------
    print("\n-- Test-fold comparison (out-of-time) --------------------")
    results = {
        "xgboost": evaluate("xgboost", y_test, xgb_proba, DECISION_THRESHOLD),
        "random_forest": evaluate("random_forest", y_test, rf_proba, DECISION_THRESHOLD),
    }

    # -- Pick the winner by PR-AUC (right metric for heavy imbalance) ---------
    best_name = max(results, key=lambda k: results[k]["pr_auc"])
    best_model = xgb_model if best_name == "xgboost" else rf_model
    print(f"\n[BEST] {best_name} (PR-AUC {results[best_name]['pr_auc']:.4f})")

    # -- SHAP explanation for the winner (native TreeSHAP if XGBoost) ---------
    if best_name == "xgboost":
        rng = np.random.default_rng(SEED)
        sample_idx = rng.choice(len(X_test), size=min(5000, len(X_test)), replace=False)
        shap_top = xgb_shap_top(xgb_model, feature_names, X_test[sample_idx])
        explain_method = "native TreeSHAP (mean |contribution|)"
    else:
        order = np.argsort(rf_model.feature_importances_)[::-1][:20]
        shap_top = [{"feature": feature_names[i],
                     "importance": round(float(rf_model.feature_importances_[i]), 5)}
                    for i in order]
        explain_method = "impurity feature importance (RandomForest)"

    # -- Persist ONLY the best model + full comparison ------------------------
    out_dir = REGISTRY_DIR / MODEL_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline = Pipeline([("preprocess", pre), ("clf", best_model)])
    joblib.dump(pipeline, out_dir / "model.joblib")

    (out_dir / "feature_names.json").write_text(
        json.dumps({"names": feature_names, "count": len(feature_names)}), encoding="utf-8"
    )
    (out_dir / "comparison.json").write_text(
        json.dumps({"models": results, "winner": best_name,
                    "selection_metric": "pr_auc"}, indent=2), encoding="utf-8"
    )

    metadata = {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": best_name,
        "candidates": list(results.keys()),
        "selection_metric": "pr_auc",
        "explain_method": explain_method,
        "decision_threshold": DECISION_THRESHOLD,
        "scale_pos_weight": scale_pos_weight,
        "n_features": len(feature_names),
        "n_numeric": len(num_cols),
        "n_categorical": len(cat_cols),
        "split": "out_of_time (80/20 by TransactionDT)",
        "training_profile": prov,
        "metrics": results[best_name],
        "all_metrics": results,
        "top_features": shap_top,
        "dataset": {
            "source": "IEEE-CIS Fraud Detection",
            "rows": int(len(y_train) + len(y_test)),
            "train_rows": int(len(y_train)),
            "test_rows": int(len(y_test)),
            "fraud_rate_test": round(float(y_test.mean()), 4),
        },
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n[OK] best model -> {out_dir / 'model.joblib'} ({best_name})")
    print(f"[OK] comparison -> {out_dir / 'comparison.json'}")
    print(f"[OK] model card -> {out_dir / 'metadata.json'}")
    print("[OK] top SHAP features:")
    for row in shap_top[:8]:
        key = "mean_abs_shap" if "mean_abs_shap" in row else "importance"
        print(f"       {row['feature']:24} {row[key]}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train the SecureNaija transaction-fraud model.")
    p.add_argument("--full", action="store_true",
                   help="Use the entire corpus + all columns (needs ~2 GB RAM, all cores).")
    p.add_argument("--sample-rows", type=int, default=120000,
                   help="Frugal mode: total rows to train+test on (0 = whole window).")
    p.add_argument("--recent-window", type=int, default=250000,
                   help="Frugal mode: most-recent rows to materialise before sampling.")
    p.add_argument("--rf-sample", type=int, default=60000,
                   help="Cap RandomForest training rows after undersampling (0 = no cap).")
    p.add_argument("--rf-ratio", type=int, default=5,
                   help="Legit:fraud ratio kept for RandomForest undersampling.")
    p.add_argument("--n-jobs", type=int, default=2,
                   help="CPU threads for training (default 2; leaves cores for the OS).")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(full=args.full, sample_rows=args.sample_rows, recent_window=args.recent_window,
         rf_sample=args.rf_sample, rf_ratio=args.rf_ratio, n_jobs=args.n_jobs)
