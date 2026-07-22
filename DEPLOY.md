# Deploying SecureNaija

Two managed services, connected from a single GitHub repo:

- **Railway** → FastAPI API + PostgreSQL (the `apps/api` service + a Postgres plugin)
- **Vercel** → Next.js web app (`apps/web`), pointed at the Railway API URL

The trained models (~1.7 MB) are committed and baked into the API image, so the
API serves out of the box — no model download or volume needed.

---

## 1. Push to GitHub

```bash
git add .
git commit -m "SecureNaija: production-ready"
git remote add origin https://github.com/<you>/securenaija.git
git push -u origin main
```

## 2. Railway — API + Postgres

1. **New Project → Deploy from GitHub repo** → pick this repo.
2. Add a **PostgreSQL** database (Railway → *New → Database → PostgreSQL*).
3. On the **API service → Settings**:
   - **Root Directory:** `/` (repo root — the build context the Dockerfile expects)
   - **Dockerfile Path:** `infra/api.Dockerfile`
4. On the **API service → Variables**, set:
   ```
   API_ENV=production
   DATABASE_URL=${{Postgres.DATABASE_URL}}   # Railway reference; psycopg driver:
   # if the ref uses postgresql://, change the scheme to postgresql+psycopg://
   JWT_SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(48))">
   CORS_ORIGINS=https://<your-vercel-domain>
   FEEDBACK_DIR=/data/feedback
   ```
   Attach a **Volume** mounted at `/data/feedback` so continuous-learning feedback
   survives redeploys.
5. Deploy. The container runs `alembic upgrade head` then `uvicorn` on `$PORT`.
   Health check: `GET /api/v1/health/ready` (returns 503 until DB + model are up).
6. Note the public API URL, e.g. `https://securenaija-api.up.railway.app`.

> `API_ENV=production` activates the fail-fast guard (rejects the default JWT
> secret / dev DB password), disables `/docs`, and adds HSTS.

## 3. Vercel — Web

1. **Add New → Project** → import the same repo.
2. **Root Directory:** `apps/web` (Vercel auto-detects Next.js).
3. **Environment Variable:**
   ```
   NEXT_PUBLIC_API_BASE_URL=https://securenaija-api.up.railway.app
   ```
   (Inlined at build time — redeploy after changing it.)
4. Deploy. Then add the Vercel domain to the API's `CORS_ORIGINS` (step 2.4) and
   redeploy the API.

## 4. Local — one command (Docker)

```bash
cp .env.example .env      # fill JWT_SECRET_KEY; keep DATABASE_URL on the db service
docker compose up --build # web :3000 · api :8000 · postgres (internal only)
```

## 5. Local — no Docker (SQLite)

```bash
# API
cd apps/api
DATABASE_URL="sqlite:///./securenaija_dev.db" API_ENV=development \
  MODEL_REGISTRY_DIR="../../ml/models" uvicorn app.main:app --port 8000
# Web (separate shell)
cd apps/web && npm run dev   # http://localhost:3000
```

---

## Scaling notes (multi-replica)

Single instance works as-is. Before running **more than one** API replica:

- Set `RATELIMIT_STORAGE_URI=redis://…` so rate limits are shared.
- Swap the in-process `EventBroker` (`app/infrastructure/realtime/broker.py`) for a
  Redis pub/sub adapter and move automation state to Redis — otherwise SSE clients
  only see events from the replica they hit (see the audit's scalability section).
- Run `alembic upgrade head` as a one-off release step instead of on container start.
- Enable sticky sessions for the SSE `/automation/stream` endpoint.
