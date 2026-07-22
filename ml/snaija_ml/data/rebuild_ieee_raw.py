"""Memory-bounded rebuild of ``ieee_cis.parquet`` with RAW numeric values.

The full ``train_transaction.csv`` is ~683MB; loading it whole needs several GB of
RAM. This reads it in **chunks** and keeps a deterministic 1-in-N subsample
(default ~20%, ~118k rows, preserving the natural ~3.5% fraud rate), merges
identity, and cleans with the shared tabular cleaner — which no longer z-scores,
so the parquet holds raw values that match what the API sends at inference
(fixes the train/serve skew). Peak memory stays a few hundred MB.

Run on a machine/CI with a bit of RAM to spare, then retrain:
    python -m snaija_ml.data.rebuild_ieee_raw --every 5
    python -m snaija_ml.pipelines.train_transaction_fraud
"""

from __future__ import annotations

import argparse

import pandas as pd

from .preprocess import PROCESSED, RAW, _downcast, clean_tabular_dataset


def run(every: int = 5, chunksize: int = 40000) -> None:
    base = RAW / "ieee_cis"
    tx = base / "train_transaction.csv"
    if not tx.exists():
        raise SystemExit(f"missing {tx} - download the IEEE-CIS data first")

    print(f"-> chunked subsample of {tx.name} (keep 1 in {every}) ...")
    parts: list[pd.DataFrame] = []
    for i, chunk in enumerate(pd.read_csv(tx, low_memory=False, chunksize=chunksize)):
        sub = chunk.iloc[(i % every)::every]
        parts.append(_downcast(sub))
        if i % 4 == 0:
            print(f"   chunk {i}: running total {sum(len(p) for p in parts):,} rows")
    df = pd.concat(parts, ignore_index=True)
    del parts

    idp = base / "train_identity.csv"
    if idp.exists():
        df = df.merge(_downcast(pd.read_csv(idp, low_memory=False)),
                      on="TransactionID", how="left")

    print(f"-> subsample {len(df):,} rows x {df.shape[1]} cols; "
          f"fraud {df['isFraud'].mean() * 100:.2f}%")
    clean, _stats = clean_tabular_dataset(df, target_col="isFraud")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / "ieee_cis.parquet"
    clean.to_parquet(out, index=False)
    print(f"[OK] wrote {out} ({len(clean):,} x {clean.shape[1]}, RAW values)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Memory-safe RAW rebuild of the IEEE parquet.")
    ap.add_argument("--every", type=int, default=5, help="Keep 1 in N rows (default 5 ~ 20%%).")
    ap.add_argument("--chunksize", type=int, default=40000)
    args = ap.parse_args()
    run(every=args.every, chunksize=args.chunksize)
