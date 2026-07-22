"""Fine-tune DistilBERT for scam detection - the optional deep upgrade to Model 1.

Not part of the default (CPU-only, offline) pipeline: torch + transformers are
imported lazily and this script only runs when you have installed them. Enable:

    uv pip install -e ".[transformers]"                 # from ml/  (~2GB, do it on wifi)
    python -m snaija_ml.pipelines.train_scam_transformer

It fine-tunes ``distilbert-base-uncased`` on the SAME processed corpora as the
linear model (Nigeria fraud SMS + UCI SMS Spam), evaluates on a held-out fold,
and saves a HuggingFace model directory to ``models/scam_transformer/`` that
``serving/scam_transformer.py`` serves with the shared ScamPrediction contract.

The base weights download from the HuggingFace hub on first run (cached
thereafter). Everything else is offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

from ..data.training_data import TrainingDataConfig, load_training_frame

MODEL_NAME = "scam_transformer"
BASE_MODEL = "distilbert-base-uncased"
SEED = 42
REGISTRY_DIR = Path(__file__).resolve().parents[2] / "models"


def main(epochs: int = 3, batch_size: int = 16, lr: float = 2e-5) -> None:
    # Lazy heavy imports - keep the package importable without torch.
    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    print("-> Loading scam corpus ...")
    df, info = load_training_frame(TrainingDataConfig())
    texts = df["text"].astype(str).tolist()
    labels = df["label"].astype(int).tolist()
    print(f"   {len(texts):,} messages from {info['sources']}")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, stratify=labels, random_state=SEED)

    tok = AutoTokenizer.from_pretrained(BASE_MODEL)

    def tokenize(batch):
        return tok(batch["text"], truncation=True, max_length=128)

    train_ds = Dataset.from_dict({"text": X_train, "label": y_train}).map(tokenize, batched=True)
    test_ds = Dataset.from_dict({"text": X_test, "label": y_test}).map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=2)

    out_dir = REGISTRY_DIR / MODEL_NAME
    args = TrainingArguments(
        output_dir=str(out_dir / "_checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=lr,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=50,
        seed=SEED,
        report_to=[],
    )

    trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=test_ds)
    print("-> Fine-tuning DistilBERT ...")
    trainer.train()

    # -- Honest evaluation on the held-out fold -------------------------------
    logits = trainer.predict(test_ds).predictions
    proba = torch.softmax(torch.tensor(logits), dim=-1)[:, 1].numpy()
    roc = roc_auc_score(y_test, proba)
    ap = average_precision_score(y_test, proba)
    print(f"-- Test: ROC-AUC {roc:.4f}  PR-AUC {ap:.4f}")

    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out_dir))
    tok.save_pretrained(str(out_dir))
    (out_dir / "metadata.json").write_text(json.dumps({
        "name": MODEL_NAME, "version": "distilbert-1.0.0", "base_model": BASE_MODEL,
        "labels": ["Safe/Suspicious", "Scam"],
        "metrics": {"roc_auc": round(float(roc), 4), "pr_auc": round(float(ap), 4)},
        "dataset": {"sources": info["sources"]},
    }, indent=2), encoding="utf-8")
    print(f"[OK] fine-tuned DistilBERT -> {out_dir}")


if __name__ == "__main__":
    main()
