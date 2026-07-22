# SecureNaija API image. Build context = repo root.
# Multi-stage: build deps with a toolchain, ship a slim non-root runtime.

# ---------- builder ----------
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the ML package first (changes least often -> better layer caching).
COPY ml /ml
RUN pip install /ml
# Then the API deps (strip the editable `-e ../../ml` line already satisfied above).
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN grep -v '^-e ' /tmp/requirements.txt > /tmp/req.txt && pip install -r /tmp/req.txt

# ---------- runtime ----------
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    FEEDBACK_DIR=/data/feedback
# libgomp1 = OpenMP runtime for XGBoost/scikit-learn; curl for the healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser

COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY apps/api /app
# Trained models are baked in when present (see .dockerignore / DEPLOY.md).
COPY ml/models /models
RUN mkdir -p /data/feedback && chown -R appuser:appuser /app /data /models
ENV MODEL_REGISTRY_DIR=/models

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health/ready || exit 1

# Migrations run on start (fine for a single instance / Railway service). For
# multi-replica, run `alembic upgrade head` as a separate release step instead.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
