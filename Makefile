.PHONY: help setup setup-backend setup-frontend migrate ingest dev dev-api dev-web test test-backend typecheck-frontend lint clean

PY ?= python3.12
VENV := backend/.venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON := $(VENV_BIN)/python

help:
	@echo "AlphaDesk make targets:"
	@echo "  setup         install backend + frontend deps + copy .env"
	@echo "  migrate       run alembic migrations"
	@echo "  ingest        fetch all funds + benchmarks and upsert"
	@echo "  dev           start API + Vite dev server (two terminals)"
	@echo "  dev-api       start uvicorn only (http://localhost:8000)"
	@echo "  dev-web       start Vite only  (http://localhost:5173)"
	@echo "  test          run pytest"
	@echo "  lint          ruff check backend"
	@echo "  typecheck     mypy backend"

setup: setup-backend setup-frontend
	@test -f .env || cp .env.example .env
	@echo ".env ready. Run: make migrate && make ingest && make dev"

setup-backend:
	cd backend && $(PY) -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend[dev]"

setup-frontend:
	cd frontend && npm install

migrate:
	cd backend && $(VENV_BIN)/alembic upgrade head

ingest:
	cd backend && $(PYTHON) -m ingestion.cli

dev-api:
	cd backend && $(VENV_BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd frontend && npm run dev

dev:
	@echo "Run 'make dev-api' and 'make dev-web' in two terminals."

test: test-backend

test-backend:
	cd backend && $(VENV_BIN)/pytest

typecheck-frontend:
	cd frontend && npm run typecheck

lint:
	cd backend && $(VENV_BIN)/ruff check .

typecheck:
	cd backend && $(VENV_BIN)/mypy app analytics ingestion

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
