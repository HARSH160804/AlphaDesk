.PHONY: help setup setup-backend migrate ingest dev dev-api dev-web test lint typecheck clean

PY ?= python3.12
VENV := backend/.venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON := $(VENV_BIN)/python

help:
	@echo "AlphaDesk make targets:"
	@echo "  setup         install backend deps + copy .env (safe to re-run)"
	@echo "  migrate       run alembic migrations"
	@echo "  ingest        fetch all funds + benchmarks and upsert"
	@echo "  dev           start API (and prints where to run web)"
	@echo "  dev-api       start uvicorn only"
	@echo "  test          run pytest"
	@echo "  lint          ruff check backend"
	@echo "  typecheck     mypy backend"

setup: setup-backend
	@test -f .env || cp .env.example .env
	@echo ".env ready. Run: make migrate && make ingest && make dev"

setup-backend:
	cd backend && $(PY) -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend[dev]"

migrate:
	cd backend && $(VENV_BIN)/alembic upgrade head

ingest:
	cd backend && $(PYTHON) -m ingestion.cli

dev-api:
	cd backend && $(VENV_BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev: dev-api

test:
	cd backend && $(VENV_BIN)/pytest

lint:
	cd backend && $(VENV_BIN)/ruff check .

typecheck:
	cd backend && $(VENV_BIN)/mypy app analytics ingestion

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
