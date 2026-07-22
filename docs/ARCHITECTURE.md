# Architecture

SecureNaija is a monorepo with three bounded contexts — **web**, **api**, and
**ml** — plus infrastructure. This document explains how they fit together and why.

## High-level flow

```
 ┌──────────────┐      HTTPS/JSON      ┌───────────────────────────┐
 │  Next.js web │ ───────────────────▶ │  FastAPI (Clean Arch)     │
 │  (browser)   │ ◀─────────────────── │  interface → application  │
 └──────────────┘   ScanResponse       │        → domain           │
                                        │  infrastructure ─┐        │
                                        └──────────────────┼────────┘
                                                           │ port
                                                           ▼
                                        ┌───────────────────────────┐
                                        │  snaija_ml (XGBoost+SHAP) │
                                        │  MessageFraudPredictor    │
                                        └───────────────────────────┘
                                                           │
                                              PostgreSQL ◀─┘ (scan history)
```

## Backend — Clean Architecture

Dependencies point inward. An inner ring never imports an outer one.

| Ring | Package | Knows about | Examples |
|------|---------|-------------|----------|
| Domain | `app.domain` | nothing | `User`, `Scan`, `FraudAssessment`, `RiskBand` |
| Application | `app.application` | domain | use cases, ports (`FraudScoringService`, `ScanRepository`) |
| Infrastructure | `app.infrastructure` | application + domain | SQLAlchemy repos, `MlFraudScoringService`, JWT/bcrypt |
| Interface | `app.interface` | all | FastAPI routers, Pydantic schemas, DI wiring |

**Why it matters:** the `DetectMessageFraud` use case depends only on the
`FraudScoringService` *port*. Today that port is fulfilled by XGBoost; swapping in
a fine-tuned Transformer means editing one file (`infrastructure/ml/scoring_service.py`)
and touching nothing else. The use-case unit tests prove this — they run with an
in-memory stub and need no database or model.

## ML — train/serve parity

`snaija_ml.common` holds the feature logic (`preprocess_for_tfidf`,
`EngineeredFeatureExtractor`) used by **both** training and serving. Because the
API imports the same `snaija_ml.serving.predictor` module that training produced,
there is no train/serve skew: identical preprocessing, identical feature order.

Explanations use XGBoost's exact TreeSHAP (`pred_contribs=True`) — the same
algorithm the `shap` library uses for tree models, but with no runtime dependency,
so a verdict always comes with its reasons.

## Data model

- `users` — accounts (bcrypt-hashed passwords).
- `scans` — every authenticated check, with the full `factors` JSONB for auditing
  and dashboards. Anonymous "try it" scans are scored but not stored.

## Extending to new detectors

Each new slice (phishing URL, fake POS alert) adds:
1. a training pipeline + predictor under `snaija_ml`,
2. a scoring adapter implementing a port,
3. a use case + router in the API,
4. a UI surface in the web app.

The existing rings do not change — that is the point of the structure.
