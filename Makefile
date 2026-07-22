# SecureNaija - common developer tasks.
#
# NOTE: use the project venv interpreter, never the bare `python` on PATH. On
# some Windows setups that resolves to MSYS2 Python with no ML wheels, which
# hangs/fails on numpy/scipy/xgboost. Override PY to point at your venv, e.g.
#   make train PY=ml/.venv/Scripts/python
.PHONY: help train test api web up down fmt

# Default to the ML venv interpreter (absolute, so it survives `cd`); override
# with `make <target> PY=python` to use whatever is on PATH.
PY ?= $(CURDIR)/ml/.venv/Scripts/python

help:
	@echo "SecureNaija make targets:"
	@echo "  make train   - train the message-fraud model"
	@echo "  make test    - run backend unit tests"
	@echo "  make api     - run the FastAPI dev server"
	@echo "  make web     - run the Next.js dev server"
	@echo "  make up      - docker compose up --build"
	@echo "  make down    - docker compose down"
	@echo "  (override interpreter with PY=..., e.g. make train PY=python)"

train:
	cd ml && "$(PY)" -m snaija_ml.pipelines.train_message_fraud

test:
	cd apps/api && "$(PY)" -m pytest -q

api:
	cd apps/api && "$(PY)" -m uvicorn app.main:app --reload

web:
	cd apps/web && npm run dev

up:
	docker compose up --build

down:
	docker compose down
