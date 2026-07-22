"""Assemble the Message-Fraud training corpus from the *processed* datasets.

The trainer used to build a purely synthetic template dataset. Now that the data
pipeline (`snaija_ml.data.preprocess`) produces cleaned, de-duplicated corpora,
training draws from real / semi-real sources instead:

  • Nigeria_Fraud_SMS  — Nigeria-specific scam typologies (BVN, KYC, POS, …) and
    matched hard-negative legitimate messages.
  • SMS Spam Collection — the real UCI corpus of genuine spam / ham SMS, which
    adds authentic linguistic variety so the model generalises beyond templates
    and stops scoring every message a degenerate 0 or 1.

The two are concatenated on the shared ``text``/``label`` schema, exact-duplicate
text is dropped, and (by default) the result is class-balanced by undersampling
the majority class so metrics are not skewed.

If none of the processed files exist yet (fresh checkout, pipeline not run), we
fall back to the in-memory synthetic generator so the trainer always works. Run
``python -m snaija_ml.data.preprocess`` first to train on the real corpora.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ML_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ML_ROOT / "data" / "processed"
# Continuous-learning corrections captured by the API (Automation Engine feedback).
# Honour FEEDBACK_DIR so retraining reads the SAME durable location the API writes
# to (a mounted volume in production); falls back to the local dev path otherwise.
_FEEDBACK_DIR = os.getenv("FEEDBACK_DIR")
FEEDBACK_CSV = (Path(_FEEDBACK_DIR) if _FEEDBACK_DIR else ML_ROOT / "data" / "feedback") / "feedback.csv"

# Processed corpora the trainer knows how to consume, in priority order. Each is
# a CSV with at least ``text`` and ``label`` columns produced by the preprocess
# pipeline. Balanced variants are preferred so we don't undersample twice.
_SOURCES: list[tuple[str, str]] = [
    ("nigeria_fraud_sms", "nigeria_fraud_sms.csv"),
    ("sms_spam", "sms_spam.csv"),
]


@dataclass
class TrainingDataConfig:
    """How to assemble the training frame.

    balance:  undersample the majority class to the minority count.
    seed:     RNG seed for the balancing sample (and synthetic fallback).
    sources:  restrict to a subset of source keys (default: all available).
    """

    balance: bool = True
    seed: int = 20260721
    sources: tuple[str, ...] | None = None


def _read_source(filename: str) -> pd.DataFrame | None:
    path = PROCESSED / filename
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if "text" not in df.columns or "label" not in df.columns:
        return None
    df = df[["text", "label"]].copy()
    df["text"] = df["text"].astype(str)
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    return df[df["text"].str.strip() != ""]


def _read_feedback() -> pd.DataFrame | None:
    """User Safe/Scam corrections captured by the Automation Engine.

    Mapped to the shared ``text``/``label`` schema (Scam=1, Safe=0) so retraining
    learns from real human-in-the-loop feedback with no code changes.
    """
    if not FEEDBACK_CSV.exists():
        return None
    try:
        df = pd.read_csv(FEEDBACK_CSV)
    except Exception:  # noqa: BLE001
        return None
    if "text" not in df.columns or "label" not in df.columns:
        return None
    df = df[["text", "label"]].copy()
    df["text"] = df["text"].astype(str)
    mapping = {"scam": 1, "safe": 0, "1": 1, "0": 0, "fraud": 1, "legit": 0}
    df["label"] = df["label"].astype(str).str.strip().str.lower().map(mapping)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    return df[df["text"].str.strip() != ""]


def _balance(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    counts = df["label"].value_counts()
    n = int(counts.min())
    parts = [g.sample(n=n, random_state=seed) for _, g in df.groupby("label")]
    return pd.concat(parts)


def load_training_frame(config: TrainingDataConfig | None = None) -> tuple[pd.DataFrame, dict]:
    """Return ``(frame[text,label], info)``.

    ``info`` records which sources were used and the row counts, so the trainer
    can stamp it into the model card for provenance.
    """
    config = config or TrainingDataConfig()
    wanted = set(config.sources) if config.sources else None

    frames: list[pd.DataFrame] = []
    per_source: dict[str, int] = {}
    for key, filename in _SOURCES:
        if wanted is not None and key not in wanted:
            continue
        df = _read_source(filename)
        if df is not None and len(df):
            df = df.assign(source=key)
            frames.append(df)
            per_source[key] = len(df)

    # Continuous learning: fold in captured user feedback (Safe/Scam corrections).
    if wanted is None or "user_feedback" in wanted:
        fb = _read_feedback()
        if fb is not None and len(fb):
            frames.append(fb.assign(source="user_feedback"))
            per_source["user_feedback"] = len(fb)

    if not frames:
        # Fallback: synthetic generator (keeps the trainer runnable pre-pipeline).
        from ..pipelines.dataset import build_dataset

        df = build_dataset()
        df["source"] = "synthetic"
        info = {
            "origin": "synthetic_fallback",
            "sources": {"synthetic": len(df)},
            "note": "Processed corpora not found; ran synthetic generator. "
                    "Run `python -m snaija_ml.data.preprocess` to train on real data.",
            "balanced": True,
            "rows_total": len(df),
            "n_fraud": int(df["label"].sum()),
            "n_legit": int((df["label"] == 0).sum()),
        }
        return df[["text", "label"]].reset_index(drop=True), info

    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["text"]).reset_index(drop=True)
    dupes = before - len(combined)

    if config.balance:
        combined = _balance(combined, config.seed)

    combined = combined.sample(frac=1, random_state=config.seed).reset_index(drop=True)

    info = {
        "origin": "processed_corpora",
        "sources": per_source,
        "duplicates_removed": int(dupes),
        "balanced": bool(config.balance),
        "rows_total": len(combined),
        "n_fraud": int(combined["label"].sum()),
        "n_legit": int((combined["label"] == 0).sum()),
    }
    return combined[["text", "label"]], info


if __name__ == "__main__":
    frame, meta = load_training_frame()
    print(meta)
    print(frame["label"].value_counts().to_string())
    print(frame.sample(min(8, len(frame)), random_state=1).to_string(index=False))
