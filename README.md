# AlphaDesk

Institutional-grade mutual fund performance analytics and automated client reporting for Indian mutual funds.

Pulls NAV history for ~30 Direct Plan - Growth schemes from [mfapi.in](https://api.mfapi.in/) and benchmark data via yfinance, computes performance and risk metrics, surfaces them in a premium web dashboard, and generates client-ready PowerPoint decks and Word reports with one click.

## Status

Phase 1 complete: repo scaffold, Docker Compose, DB schema + migrations, ingestion with validation.
Phase 2+ (metrics, SQL, API, UI, reports) to follow.

## Quickstart

```bash
make setup       # creates backend/.venv, installs deps, writes .env
make migrate     # runs alembic upgrade head
make ingest      # fetches NAVs for all funds + benchmarks
make dev         # starts the API at http://localhost:8000
```

Three commands past `make setup` and the full pipeline runs. The API comes up with Swagger UI at `/docs`.

With Docker:

```bash
docker compose up --build
```

## What's in Phase 1

- **DB schema** (SQLAlchemy 2.0 + Alembic): `funds`, `benchmarks`, `nav_history`, `benchmark_history`, `ingestion_runs`, with proper keys, indexes and check constraints. Postgres in Docker, SQLite fallback for local dev (set via `DATABASE_URL`).
- **Fund universe** (`config/funds.yaml`): 29 real schemes across Large Cap, Mid Cap, Small Cap, Flexi Cap, Index and Short Duration Debt. Every `scheme_code` verified against the API before being added.
- **Ingestion** (`backend/ingestion/`):
  - `mfapi_client.py` with rate limiting, exponential-backoff retries via `tenacity`, and a strict parser.
  - `benchmark_client.py` for yfinance pulls (Nifty 50, Midcap 150, Smallcap 250).
  - `validate.py` catches non-positive NAVs, duplicate dates and gaps > 7 days — nothing is silently dropped; everything shows up in the `ingestion_runs` row.
  - `pipeline.py` is **idempotent**: safe to re-run, upserts only (dialect-aware for Postgres and SQLite).
- **Config** via `pydantic-settings`, loaded from `.env` + env vars.
- **FastAPI** stub with `/healthz` and `/api/stats` so the stack is wired end-to-end today.
- **Tests** for the validator and universe loader (`pytest`).

## Project layout

```
AlphaDesk/
├── backend/
│   ├── alembic/            Alembic migrations
│   ├── app/                FastAPI app, config, models, DB
│   ├── analytics/          Metrics (Phase 2)
│   ├── ingestion/          mfapi + yfinance pipeline
│   ├── reports/            PPTX / DOCX report generator (Phase 7)
│   ├── sql/                Analyst-style SQL (Phase 3)
│   ├── tests/              pytest
│   ├── Dockerfile
│   └── pyproject.toml
├── config/
│   └── funds.yaml          Fund universe (scheme code → category → benchmark)
├── docker-compose.yml
├── Makefile
└── frontend/               React 18 + Vite (Phase 5+)
```

## Fund universe

| Category | Count |
| --- | --- |
| Large Cap | 6 |
| Mid Cap | 5 |
| Small Cap | 5 |
| Flexi Cap | 4 |
| Index | 4 |
| Short Duration Debt | 5 |
| **Total** | **29** |

Each row in `config/funds.yaml` carries `{scheme_code, category, benchmark_id}`. Fund metadata (name, AMC, mfapi scheme category) is fetched during ingestion and written to the `funds` table — the YAML stays small and auditable.

## Verifying Phase 1

```bash
make setup
make migrate
make ingest

# Expect: ~29 funds processed, ~100k NAV rows upserted, ~3 benchmarks
# (CRISIL_SHORT_BOND has no public yf ticker and is skipped with a warning.)

sqlite3 data/alphadesk.db "SELECT category, COUNT(*) FROM funds GROUP BY category;"
sqlite3 data/alphadesk.db "SELECT COUNT(*) FROM nav_history;"
sqlite3 data/alphadesk.db "SELECT status, rows_inserted, warnings FROM ingestion_runs;"

make test
```

## Design decisions (Phase 1)

- **SQLite fallback over postgres-only.** Keeps local dev `make setup && make ingest` under 60s with zero infra. Postgres path stays authoritative (docker-compose). Upserts are dialect-aware so neither path degrades.
- **Idempotent ingestion, no truncate-and-reload.** Re-running `make ingest` is cheap and safe; it only writes new or changed rows. This matters when the pipeline is scheduled.
- **Audit trail first.** The `ingestion_runs` table is written at the start of a run, not the end, so a crash still leaves evidence. Validation warnings land there verbatim.
- **Fund universe in YAML, metadata from the API.** The YAML stays authoritative for category/benchmark mapping (an analyst's choice) and lets the ingest discover scheme names from mfapi — so a cosmetic rename upstream doesn't need a code change.

## Roadmap

- [x] Phase 1: scaffold, DB schema, ingestion with validation
- [ ] Phase 2: metrics module + pytest suite
- [ ] Phase 3: SQL analysis files + insights notebook
- [ ] Phase 4: FastAPI endpoints + tests
- [ ] Phase 5: design system + `/design` route
- [ ] Phase 6: dashboard pages
- [ ] Phase 7: PPTX + DOCX report generation
- [ ] Phase 8: README polish, screenshots, final pass
