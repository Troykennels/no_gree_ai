# SecureNaija ML — the AI Engine

Datasets, training pipelines, and serving for the SecureNaija fraud-intelligence
platform. Installed as `snaija_ml` and imported directly by the API, so training
and serving share identical feature logic (**no train/serve skew**).

The engine ships **three** models:

| # | Model | Task | Algorithm | Serves |
|---|-------|------|-----------|--------|
| — | **Message Fraud** | SMS/WhatsApp/loan text → fraud score | TF-IDF + 13 Nigeria signals → XGBoost (Platt-calibrated) | `serving/predictor.py` |
| **1** | **Scam Detection** | message → Safe / Suspicious / Scam | TF-IDF (1–2 gram) → Logistic Regression | `serving/scam_predictor.py` |
| **2** | **Transaction Fraud** | card transaction → fraud | XGBoost vs RandomForest (best kept) | `serving/transaction_predictor.py` |

> Optional deep upgrade to Model 1: fine-tuned **DistilBERT**
> (`serving/scam_transformer.py`) — same prediction contract, drop-in. Needs
> `torch`; install with `uv pip install -e ".[transformers]"` then
> `python -m snaija_ml.pipelines.train_scam_transformer`.

## Setup & train

```bash
uv venv --python 3.11 .venv          # standard CPython 3.11/3.12 only
uv pip install -e .                   # (MSYS2/MinGW & legacy Anaconda lack ML wheels)

# one-time data prep (the ONLY network step; cached afterwards)
python -m snaija_ml.data.preprocess

# train
python -m snaija_ml.pipelines.train_scam_detection        # Model 1
python -m snaija_ml.pipelines.train_transaction_fraud     # Model 2  (frugal by default)
python -m snaija_ml.pipelines.train_message_fraud         # original text model

python smoke_test.py                  # sanity-check Model-1-style scoring
```

### Low-RAM machines (≈8 GB)

`train_transaction_fraud` is **frugal by default** so it never thrashes a laptop:
it reads only a curated column subset via Arrow, materialises a recent
out-of-time window, subsamples to 120k rows, caps trees, and uses 2 cores. Every
reduction is stamped into the model card (`training_profile`). Scale up on a
bigger box:

```bash
python -m snaija_ml.pipelines.train_transaction_fraud --full            # all rows/cols (~2 GB RAM)
python -m snaija_ml.pipelines.train_transaction_fraud --sample-rows 250000 --n-jobs 4
```

## Model 1 — Scam Detection (card)

| | |
|---|---|
| **Model** | TF-IDF (1–2 gram, redacted text) + Logistic Regression, `class_weight="balanced"` |
| **Output** | 3-way label (Safe / Suspicious / Scam) from two thresholds + probability + confidence |
| **Explanations** | Exact linear contributions (`coef × tfidf`) → highlighted suspicious words + plain-English reason — no post-hoc approximation |
| **Threshold** | F2-optimal (recall-weighted); suspicious ≥ 0.21, scam ≥ 0.38 |
| **Data** | UCI SMS Spam (5153) + Nigeria fraud SMS (1140), balanced to 1193/1193 |
| **Metrics (held-out test)** | ROC-AUC **0.999**, PR-AUC 0.999, precision 0.978, recall 0.994, F1 0.986 · 5-fold CV ROC-AUC 0.992 ± 0.002 |

Metrics are honest (real corpora, real errors in the confusion matrix), not
templated. Full card: `models/scam_detection/metadata.json`.

## Model 2 — Transaction Fraud (card)

| | |
|---|---|
| **Task** | Tabular card-transaction fraud on the **IEEE-CIS** dataset |
| **Candidates** | XGBoost **vs** RandomForest, identical leakage-safe preprocessing; **winner picked by PR-AUC** (right metric for a ~3.5% base rate) |
| **Split** | **Out-of-time** (train on the past, test on the most recent 20% by `TransactionDT`) — no future leakage |
| **Explanations** | Native TreeSHAP (`pred_contribs`) — per-transaction, signed (raises vs lowers risk) |
| **Winner** | **XGBoost** |

Comparison on the untouched out-of-time test fold (120k-row frugal profile):

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|-------|:-------:|:------:|:---------:|:------:|:--:|
| **XGBoost** (kept) | **0.923** | **0.681** | 0.485 | 0.749 | 0.589 |
| RandomForest | 0.908 | 0.634 | 0.386 | 0.751 | 0.510 |

Top SHAP drivers: `C13, TransactionAmt, C14, C1, card1, card6, D1, card2, V70…`
Only the best model is persisted, alongside `comparison.json` and a full model
card in `models/transaction_fraud/metadata.json`.

## Serving contract

Each predictor loads once (process-wide singleton) and returns a dataclass the
API maps straight to JSON:

- **Scam** → `label, scam_probability, confidence, highlighted_words[], explanation`
- **Transaction** → `fraud_probability, is_fraud, decision (approve/review/decline), risk_band, factors[] (SHAP), verdict`

Missing transaction fields are **imputed exactly as in training**, so a caller can
send only the fields it knows and still get a calibrated score.

## Layout

```
snaija_ml/
├── common/       feature extraction + text normalization (shared train & serve)
├── data/         download + preprocess (UCI SMS, IEEE-CIS) → data/processed/
├── pipelines/    train_scam_detection · train_transaction_fraud · train_message_fraud
│                 (+ train_scam_transformer — optional DistilBERT)
└── serving/      scam_predictor · transaction_predictor · predictor (+ scam_transformer)
models/           trained artifacts per model (model.joblib, metadata.json, …)
```
