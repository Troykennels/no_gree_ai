# SecureNaija AI

> AI-powered fraud intelligence that protects Nigerians from digital fraud **before** money is lost.

SecureNaija predicts fraud instead of reacting to it — a two-model **AI Engine**:

- **Model 1 · Scam Detection** — paste a suspicious SMS/WhatsApp/loan message and get a
  Safe / Suspicious / Scam verdict, the exact suspicious words highlighted, and a
  human-readable explanation. (TF-IDF + Logistic Regression; optional DistilBERT upgrade.)
- **Model 2 · Transaction Fraud** — score a card transaction (IEEE-CIS) as
  approve / review / decline with a calibrated fraud probability and a per-transaction
  SHAP explanation. (XGBoost, selected over RandomForest by PR-AUC.)

Every score comes with the *why*, so it's decision support a human can trust.

---

## Monorepo layout

```
securenaija/
├── apps/
│   ├── web/                 # Next.js 15 · TypeScript · Tailwind · shadcn/ui · Framer · React Query · Recharts
│   └── api/                 # FastAPI · Clean Architecture · SQLAlchemy · Alembic · JWT
├── ml/                      # Training pipelines · model registry · SHAP explainers · serving
├── packages/
│   └── shared-types/        # Shared API contract types
├── infra/                   # docker-compose, database, CI
└── docs/                    # Architecture decision records & guides
```

## Architecture

The backend follows **Clean Architecture**. Dependencies point inward only:

```
interface (FastAPI routers, schemas)
   └── application (use cases, ports/interfaces, DTOs)
          └── domain (entities, value objects, business rules)
   infrastructure (DB repos, ML adapter, security) implements application ports
```

The ML system is a separate bounded context. The API talks to it through scoring
ports, so an underlying model (XGBoost today, a Transformer tomorrow) can change
without touching a single line of API or UI code.

## The AI Engine — models & endpoints

| Model | Task | Algorithm | Test metrics | API endpoint | Web page |
|-------|------|-----------|--------------|--------------|----------|
| **1 · Scam Detection** | text → Safe/Suspicious/Scam | TF-IDF + Logistic Regression | ROC-AUC 0.999 · F1 0.986 | `POST /api/v1/scam/detect` | `/scam` |
| **2 · Transaction Fraud** | card txn → fraud | XGBoost (vs RandomForest, PR-AUC-selected) | ROC-AUC 0.923 · PR-AUC 0.681 | `POST /api/v1/transaction/score` | `/transaction` |
| Message Fraud | text → fraud score | TF-IDF + signals → XGBoost | (see model card) | `POST /api/v1/fraud/detect` | `/detector` |

Engine readiness of all models: `GET /api/v1/engine/status`. Model 2 accepts a
**partial** feature map — anything omitted is imputed exactly as in training, so a
couple of fields still returns a score. Full model cards live in
`ml/models/<model>/metadata.json`; metrics are honest (real data, real errors),
not templated. Details and the RandomForest-vs-XGBoost comparison: `ml/README.md`.

## The Fraud Intelligence Engine — one score, one plan

Fuses **both** models into a single verdict. Send a message, a transaction, or
both to `POST /api/v1/intelligence/assess` and get back, instantly:

- an **overall risk score 0–100** (independent signals combined with noisy-OR,
  plus severity floors so one strong signal is never diluted),
- a **category** — Safe · Low · Medium · High · Critical,
- the **signals** that fired (malicious link, credential request, transaction
  decline, urgency, …), and
- prioritised **AI recommendations** — *"Do not click the link"*, *"Freeze your
  card"*, *"Contact your bank"*, *"Change your PIN"*, *"Enable Two-Factor
  Authentication"* — each traceable to the signal that triggered it.

Deterministic and explainable (rules over detected signals), which is the right
property for advice about someone's money. Web page: `/intelligence`.

## The Automation Engine — everything updates automatically

An always-on, event-driven layer sits on top of the models. Every scored message
or transaction flows through the engine, which updates the live state and pushes
it to every connected browser over **Server-Sent Events** — no manual refresh.

Pipeline (per event): **AI scans → risk score → alert (if a threat) → security
score recalculated → timeline, heatmap & stats updated → notification pushed**.
The **Command Center** (`/monitor`) renders it all live.

| Endpoint | What it does |
|----------|--------------|
| `GET /api/v1/automation/stream` | **SSE** live feed the dashboard subscribes to |
| `GET /api/v1/automation/snapshot` | Full current state (initial paint / polling fallback) |
| `POST /api/v1/automation/ingest/message` | Score a message → updates everything live |
| `POST /api/v1/automation/ingest/transaction` | Score a transaction → updates everything live |
| `POST /api/v1/automation/simulate` | Drive a realistic live demo feed (for sales) |
| `POST /api/v1/automation/feedback` | Mark **Safe/Scam** → continuous learning |
| `GET /api/v1/automation/report/daily` | Auto-generated daily security report |

- **Auto-recalc:** a background heartbeat recomputes the **security score** and
  regenerates the **daily report** on a timer (FastAPI lifespan task).
- **Continuous learning:** feedback is appended to `ml/data/feedback/feedback.csv`,
  which `train_scam_detection` reads as an extra source — so the next training run
  learns from real human corrections. Point `FEEDBACK_DIR` at a mounted volume in
  production.
- **Scaling:** the live state is an in-memory pub/sub (`infrastructure/realtime`,
  `infrastructure/automation`). Swap the single `EventBroker` for a Redis adapter
  behind the same `publish`/`subscribe` surface to run multiple API replicas.

## Quick start

> **Interpreter note:** use **standard CPython 3.11 or 3.12** (python.org or pyenv)
> for the venv, or just use Docker. An MSYS2/MinGW Python or a legacy Anaconda
> will not find prebuilt wheels for numpy/scipy/xgboost and the install will fail.

### 1. Train the models (optional — trained models already ship in `ml/models/`)

```bash
cd ml
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
python -m snaija_ml.data.preprocess                     # one-time data prep (cached)
python -m snaija_ml.pipelines.train_scam_detection      # Model 1  -> ml/models/scam_detection/
python -m snaija_ml.pipelines.train_transaction_fraud   # Model 2  -> ml/models/transaction_fraud/  (frugal by default)
python smoke_test_engine.py                             # verify all models in one command
```

> `train_transaction_fraud` is **laptop-safe by default** (curated columns,
> recent-window subsample, 2 cores). On an 8 GB machine it trains in a couple of
> minutes without swapping. Use `--full` on a bigger box for the whole corpus.

> The trainer reads already-processed corpora under `ml/data/processed/` (built
> once by `python -m snaija_ml.data.preprocess`) and makes **no network calls**.
> Only `preprocess` downloads source datasets; it caches them, so it never
> re-downloads.

### 2. Run everything with Docker

```bash
cp .env.example .env
docker compose up --build
```

- Web:  http://localhost:3000
- API:  http://localhost:8000  (docs at `/docs`)
- DB:   localhost:5432

### 3. Run locally without Docker

The API needs a running Postgres for auth + saved history (the anonymous
"try it" scan works without one). Start Postgres, then point `DATABASE_URL` at
`localhost` (not the `db` compose hostname):

```bash
# 0. Postgres (quickest: just the db service from compose)
docker compose up -d db
export DATABASE_URL="postgresql+psycopg://securenaija:securenaija_dev_password@localhost:5432/securenaija"

# API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Web (new terminal)
cd apps/web
npm install
npm run dev
```

## Roadmap (vertical slices)

- [x] **Message Fraud Detector** — SMS / WhatsApp / loan-offer text analysis
- [x] **Model 1 — Scam Detection** — Safe / Suspicious / Scam + highlighted words
- [x] **Model 2 — Transaction Fraud** — IEEE-CIS, XGBoost vs RandomForest, SHAP
- [ ] DistilBERT upgrade for Model 1 (code ready in `serving/scam_transformer.py`)
- [ ] Phishing URL Scanner
- [ ] Fraud Intelligence Dashboard (trends, threat map)
- [ ] Bank / Fintech ingestion API + webhooks

## License

Proprietary — © SecureNaija.
