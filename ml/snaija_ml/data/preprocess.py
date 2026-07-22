"""Preprocessing pipeline for every SecureNaija dataset.

For each available dataset this pipeline handles:

  • missing values      (drop empty text rows / impute tabular columns)
  • duplicates          (exact-duplicate removal)
  • outliers            (length-IQR for text, value-IQR winsorizing for tabular)
  • class imbalance      (report ratio + write a class-balanced copy)
  • normalization        (text normalize / StandardScaler for tabular numerics)
  • tokenization         (word tokens + token counts for text)

It then writes the processed datasets, a machine-readable report
(`data/reports/dataset_report.json`), and chart PNGs
(`data/reports/charts/`), and mirrors both into the web app's public folder so
the admin page can render them with no backend running.

Run:  python -m snaija_ml.data.preprocess
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ..common.text import normalize  # noqa: E402

ML_ROOT = Path(__file__).resolve().parents[2]
DATA = ML_ROOT / "data"
GENERATED = DATA / "generated"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
REPORTS = DATA / "reports"
CHARTS = REPORTS / "charts"
WEB_PUBLIC = ML_ROOT.parent / "apps" / "web" / "public" / "reports"

_TOKEN_RE = re.compile(r"[a-z0-9_]+")

# Brand palette (works on the dark admin page).
C_FRAUD = "#ef4444"
C_LEGIT = "#10b981"
C_ACCENT = "#38bdf8"
C_MUTED = "#94a3b8"
C_GRID = "#1e293b"
C_BG = "#0b1220"


# ─────────────────────────────────────────────────────────────────────────────
# Chart helpers
# ─────────────────────────────────────────────────────────────────────────────

def _new_ax(figsize=(6, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED, labelsize=9)
    ax.yaxis.label.set_color(C_MUTED)
    ax.xaxis.label.set_color(C_MUTED)
    ax.title.set_color("#e2e8f0")
    return fig, ax


def _save(fig, name: str) -> str:
    CHARTS.mkdir(parents=True, exist_ok=True)
    path = CHARTS / name
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return f"charts/{name}"


def _bar(labels, values, title, name, colors=None, rotate=0):
    fig, ax = _new_ax((max(6, len(labels) * 0.7), 4))
    colors = colors or [C_ACCENT] * len(labels)
    ax.bar(labels, values, color=colors)
    ax.set_title(title)
    ax.grid(axis="y", color=C_GRID, linewidth=0.6)
    if rotate:
        plt.setp(ax.get_xticklabels(), rotation=rotate, ha="right")
    return _save(fig, name)


def _pie(labels, values, title, name, colors):
    fig, ax = _new_ax((5, 4))
    ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%",
           textprops={"color": "#e2e8f0", "fontsize": 9},
           wedgeprops={"edgecolor": C_BG, "linewidth": 2})
    ax.set_title(title)
    return _save(fig, name)


# ─────────────────────────────────────────────────────────────────────────────
# Text-dataset cleaning
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(normalize(text))


def clean_text_dataset(df: pd.DataFrame, text_col: str, label_col: str,
                       positive_label) -> tuple[pd.DataFrame, dict]:
    n_raw = len(df)
    missing = int(df[text_col].isna().sum() + (df[text_col].astype(str).str.strip() == "").sum())

    # Missing values -> drop empty text.
    df = df.copy()
    df[text_col] = df[text_col].astype(str)
    df = df[df[text_col].str.strip() != ""]

    # Duplicates.
    before = len(df)
    df = df.drop_duplicates(subset=[text_col])
    dupes = before - len(df)

    # Outliers by message length (IQR).
    lengths = df[text_col].str.len()
    q1, q3 = lengths.quantile(0.25), lengths.quantile(0.75)
    iqr = q3 - q1
    hi = q3 + 3 * iqr
    keep = (lengths >= 2) & (lengths <= max(hi, 40))
    outliers = int((~keep).sum())
    df = df[keep]

    # Normalization + tokenization.
    df["clean_text"] = df[text_col].map(normalize)
    df["tokens"] = df["clean_text"].map(lambda t: " ".join(_TOKEN_RE.findall(t)))
    df["token_count"] = df["tokens"].str.split().map(len)

    # Class distribution / imbalance.
    dist = df[label_col].value_counts().to_dict()
    dist = {str(k): int(v) for k, v in dist.items()}
    counts = list(dist.values())
    balance_ratio = round(min(counts) / max(counts), 3) if counts else 0.0
    n_pos = int((df[label_col] == positive_label).sum())
    positive_ratio = round(n_pos / len(df), 4) if len(df) else 0.0

    stats = {
        "rows_raw": n_raw,
        "rows_processed": len(df),
        "missing_values": missing,
        "duplicates_removed": int(dupes),
        "outliers_removed": outliers,
        "class_distribution": dist,
        "class_balance_ratio": balance_ratio,
        "positive_ratio": positive_ratio,
        "avg_token_count": round(float(df["token_count"].mean()), 2),
    }
    return df, stats


def _balance(df: pd.DataFrame, label_col: str, seed: int = 42) -> pd.DataFrame:
    """Class-balance by undersampling the majority class (keeps unique rows)."""
    counts = df[label_col].value_counts()
    n = int(counts.min())
    parts = [g.sample(n=n, random_state=seed) for _, g in df.groupby(label_col)]
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tabular-dataset cleaning (IEEE-CIS)
# ─────────────────────────────────────────────────────────────────────────────

def clean_tabular_dataset(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, dict]:
    n_raw = len(df)
    total_cells = df.size
    missing_total = int(df.isna().sum().sum())
    top_missing = (
        df.isna().mean().sort_values(ascending=False).head(15) * 100
    ).round(2).to_dict()

    df = df.copy()
    # Drop columns that are almost entirely missing.
    thresh = 0.9
    high_missing_cols = [c for c in df.columns if df[c].isna().mean() > thresh and c != target_col]
    df = df.drop(columns=high_missing_cols)

    # Duplicates.
    before = len(df)
    df = df.drop_duplicates()
    dupes = before - len(df)

    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]

    # Missing values -> impute (numeric median, categorical mode).
    for c in numeric:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].median())
    for c in categorical:
        if df[c].isna().any():
            mode = df[c].mode(dropna=True)
            df[c] = df[c].fillna(mode.iloc[0] if len(mode) else "unknown")

    # Outliers -> winsorize numeric columns to the 1st/99th percentile.
    outlier_cells = 0
    for c in numeric:
        if c == target_col:
            continue
        lo, hi = df[c].quantile(0.01), df[c].quantile(0.99)
        outlier_cells += int(((df[c] < lo) | (df[c] > hi)).sum())
        df[c] = df[c].clip(lo, hi)

    # Normalization -> standardize numeric features (z-score).
    norm_cols = [c for c in numeric if c != target_col]
    for c in norm_cols:
        std = df[c].std()
        if std and not np.isnan(std):
            df[c] = (df[c] - df[c].mean()) / std

    dist, balance_ratio, positive_ratio = {}, 0.0, 0.0
    if target_col in df.columns:
        dist = {str(k): int(v) for k, v in df[target_col].value_counts().items()}
        counts = list(dist.values())
        balance_ratio = round(min(counts) / max(counts), 4) if counts else 0.0
        positive_ratio = round(int(df[target_col].sum()) / len(df), 4) if len(df) else 0.0

    stats = {
        "rows_raw": n_raw,
        "rows_processed": len(df),
        "n_features": df.shape[1],
        "missing_values": missing_total,
        "missing_pct": round(100 * missing_total / total_cells, 2) if total_cells else 0.0,
        "top_missing_columns": top_missing,
        "high_missing_columns_dropped": len(high_missing_cols),
        "duplicates_removed": int(dupes),
        "outliers_clipped": outlier_cells,
        "class_distribution": dist,
        "class_balance_ratio": balance_ratio,
        "positive_ratio": positive_ratio,
        "imbalance_note": "Severe imbalance; use class weights or SMOTE at train time.",
    }
    return df, stats


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

def _load_nigeria() -> pd.DataFrame | None:
    p = GENERATED / "Nigeria_Fraud_SMS.csv"
    return pd.read_csv(p) if p.exists() else None


def _load_sms_spam() -> pd.DataFrame | None:
    p = RAW / "sms_spam" / "SMSSpamCollection.tsv"
    if not p.exists():
        return None
    df = pd.read_csv(p, sep="\t", header=None, names=["label_name", "text"],
                     quoting=3, on_bad_lines="skip")
    df["label"] = (df["label_name"].str.lower() == "spam").astype(int)
    return df


def _downcast(df: pd.DataFrame) -> pd.DataFrame:
    """Halve memory: float64 -> float32, int64 -> int32 where safe."""
    for c in df.select_dtypes(include=["float64"]).columns:
        df[c] = df[c].astype("float32")
    for c in df.select_dtypes(include=["int64"]).columns:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    return df


def _load_ieee() -> pd.DataFrame | None:
    base = RAW / "ieee_cis"
    tx = base / "train_transaction.csv"
    if not tx.exists():
        return None
    # 683MB / ~590k rows x 394 cols — downcast on load to keep memory in check.
    df = _downcast(pd.read_csv(tx, low_memory=False))
    idp = base / "train_identity.csv"
    if idp.exists():
        df = df.merge(_downcast(pd.read_csv(idp, low_memory=False)), on="TransactionID", how="left")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def run() -> dict:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    report: dict = {"datasets": {}, "generated_charts": []}

    # ---- Nigeria_Fraud_SMS ----
    ng = _load_nigeria()
    if ng is not None:
        clean, stats = clean_text_dataset(ng, "text", "label", positive_label=1)
        clean.to_csv(PROCESSED / "nigeria_fraud_sms.csv", index=False)
        clean.to_parquet(PROCESSED / "nigeria_fraud_sms.parquet", index=False)
        _balance(clean, "label").to_csv(PROCESSED / "nigeria_fraud_sms_balanced.csv", index=False)
        cat_dist = {str(k): int(v) for k, v in ng["category"].value_counts().items()}
        stats.update({
            "name": "Nigeria_Fraud_SMS",
            "kind": "text",
            "purpose": "Nigerian scam message detection",
            "category_distribution": cat_dist,
            "scam_ratio": stats["positive_ratio"],
        })
        report["datasets"]["nigeria_fraud_sms"] = stats
        report["generated_charts"].append(
            _bar(["Fraud", "Legit"],
                 [stats["class_distribution"].get("1", 0), stats["class_distribution"].get("0", 0)],
                 "Nigeria_Fraud_SMS - class distribution", "nigeria_class_distribution.png",
                 colors=[C_FRAUD, C_LEGIT]))
        report["generated_charts"].append(
            _pie(["Fraud", "Legit"],
                 [stats["class_distribution"].get("1", 0), stats["class_distribution"].get("0", 0)],
                 "Nigeria scam ratio", "nigeria_scam_ratio.png", colors=[C_FRAUD, C_LEGIT]))
        scam_cats = {k: v for k, v in cat_dist.items() if not k.lower().startswith("legit")}
        report["generated_charts"].append(
            _bar(list(scam_cats.keys()), list(scam_cats.values()),
                 "Nigeria scam categories", "nigeria_categories.png",
                 colors=[C_FRAUD] * len(scam_cats), rotate=40))

    # ---- SMS Spam Collection ----
    sp = _load_sms_spam()
    if sp is not None:
        clean, stats = clean_text_dataset(sp, "text", "label", positive_label=1)
        clean.to_csv(PROCESSED / "sms_spam.csv", index=False)
        clean.to_parquet(PROCESSED / "sms_spam.parquet", index=False)
        _balance(clean, "label").to_csv(PROCESSED / "sms_spam_balanced.csv", index=False)
        stats.update({
            "name": "SMS Spam Collection",
            "kind": "text",
            "purpose": "Scam / spam message detection",
            "scam_ratio": stats["positive_ratio"],
        })
        report["datasets"]["sms_spam"] = stats
        report["generated_charts"].append(
            _bar(["Spam", "Ham"],
                 [stats["class_distribution"].get("1", 0), stats["class_distribution"].get("0", 0)],
                 "SMS Spam - class distribution", "sms_spam_class_distribution.png",
                 colors=[C_FRAUD, C_LEGIT]))
        report["generated_charts"].append(
            _pie(["Spam", "Ham"],
                 [stats["class_distribution"].get("1", 0), stats["class_distribution"].get("0", 0)],
                 "SMS spam ratio", "sms_spam_ratio.png", colors=[C_FRAUD, C_LEGIT]))

    # ---- IEEE-CIS (if present) ----
    # This is the one heavy step (683MB, ~590k x 394). Guard it so an OOM or read
    # error can never abort the whole run before the report + web mirror are
    # written — the text-dataset intelligence must always land.
    ieee_error: str | None = None
    try:
        ie = _load_ieee()
    except Exception as exc:  # noqa: BLE001 - best-effort on a large optional dataset
        ie, ieee_error = None, f"{type(exc).__name__}: {exc}"
        print(f"[ieee_cis] load failed, continuing without it: {ieee_error}")

    if ie is not None:
        try:
            clean, stats = clean_tabular_dataset(ie, target_col="isFraud")
            clean.to_parquet(PROCESSED / "ieee_cis.parquet", index=False)
            stats.update({
                "name": "IEEE-CIS Fraud Detection",
                "kind": "tabular",
                "purpose": "Transaction fraud detection",
                "fraud_ratio": stats["positive_ratio"],
            })
            report["datasets"]["ieee_cis"] = stats
            report["generated_charts"].append(
                _bar(["Fraud", "Legit"],
                     [stats["class_distribution"].get("1", 0), stats["class_distribution"].get("0", 0)],
                     "IEEE-CIS - class distribution", "ieee_class_distribution.png",
                     colors=[C_FRAUD, C_LEGIT]))
            mv = stats.get("top_missing_columns", {})
            if mv:
                report["generated_charts"].append(
                    _bar(list(mv.keys()), list(mv.values()),
                         "IEEE-CIS - top missing columns (%)", "ieee_missing.png",
                         colors=[C_ACCENT] * len(mv), rotate=40))
        except Exception as exc:  # noqa: BLE001
            ieee_error = f"{type(exc).__name__}: {exc}"
            print(f"[ieee_cis] processing failed, continuing without it: {ieee_error}")

    if "ieee_cis" not in report["datasets"]:
        report["datasets"]["ieee_cis"] = {
            "name": "IEEE-CIS Fraud Detection",
            "kind": "tabular",
            "purpose": "Transaction fraud detection",
            "status": "error" if ieee_error else "not_downloaded",
            "note": (f"Could not process the IEEE-CIS files ({ieee_error})."
                     if ieee_error else
                     "Provide Kaggle credentials or drop CSVs into data/raw/ieee_cis/, "
                     "then re-run `python -m snaija_ml.data.preprocess`."),
        }

    # ---- Overview chart: dataset sizes ----
    sizes = {v.get("name", k): v.get("rows_processed", 0)
             for k, v in report["datasets"].items() if v.get("rows_processed")}
    if sizes:
        report["generated_charts"].append(
            _bar(list(sizes.keys()), list(sizes.values()),
                 "Dataset sizes (rows)", "overview_sizes.png",
                 colors=[C_ACCENT] * len(sizes), rotate=20))

    report["summary"] = {
        "total_datasets": len([d for d in report["datasets"].values()
                               if d.get("rows_processed")]),
        "total_rows": int(sum(v.get("rows_processed", 0) for v in report["datasets"].values())),
    }

    # ---- Write report + mirror to web ----
    (REPORTS / "dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _mirror_to_web()
    return report


def _mirror_to_web() -> None:
    """Copy report JSON + charts into the web app's public folder."""
    try:
        (WEB_PUBLIC / "charts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPORTS / "dataset_report.json", WEB_PUBLIC / "dataset_report.json")
        for png in CHARTS.glob("*.png"):
            shutil.copy2(png, WEB_PUBLIC / "charts" / png.name)
    except Exception as exc:  # noqa: BLE001
        print(f"[mirror] could not copy to web public: {exc}")


if __name__ == "__main__":
    rep = run()
    print(json.dumps({k: (v.get("rows_processed") or v.get("status"))
                      for k, v in rep["datasets"].items()}, indent=2))
    print(f"Charts: {len(rep['generated_charts'])}  ->  {CHARTS}")
    print(f"Report -> {REPORTS / 'dataset_report.json'}")
