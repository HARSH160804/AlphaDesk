"""FastAPI entry point. All public routes live here via mounted routers."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.db import SessionLocal
from app.logging_setup import configure_logging
from app.models import Fund, IngestionRun, NavHistory
from app.routers.categories import router as categories_router
from app.routers.compare import router as compare_router
from app.routers.funds import router as funds_router
from app.routers.ingest import router as ingest_router
from app.routers.reports import router as reports_router
from app.sql_endpoint import router as sql_router

configure_logging()

tags_metadata = [
    {"name": "funds", "description": "Fund-level metrics, series, and comparisons."},
    {"name": "categories", "description": "Peer-group aggregates."},
    {"name": "sql", "description": "Analyst SQL queries exposed by name."},
    {"name": "ingestion", "description": "Trigger and inspect NAV refresh runs."},
    {"name": "reports", "description": "Automated PPTX / DOCX report generation."},
    {"name": "meta", "description": "Health and liveness."},
]

app = FastAPI(
    title="AlphaDesk API",
    version="0.1.0",
    description=(
        "Mutual fund performance analytics and automated client reporting.\n\n"
        "Every numeric metric carries a `reason` when unavailable rather than silently returning null — "
        "the series endpoints are safe to render even on partial history."
    ),
    openapi_tags=tags_metadata,
)

# CORS: in dev the Vite frontend runs on 5173; keep the policy explicit.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)

for r in (
    funds_router,
    compare_router,
    categories_router,
    sql_router,
    ingest_router,
    reports_router,
):
    app.include_router(r)


@app.get("/healthz", tags=["meta"], summary="Liveness probe")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/stats", tags=["meta"], summary="Row counts + last ingestion snapshot")
def stats() -> dict:
    with SessionLocal() as s:
        funds = s.scalar(select(func.count()).select_from(Fund)) or 0
        navs = s.scalar(select(func.count()).select_from(NavHistory)) or 0
        latest_run = s.scalars(
            select(IngestionRun).order_by(IngestionRun.id.desc()).limit(1)
        ).first()
    return {
        "funds": funds,
        "nav_rows": navs,
        "latest_ingestion": None
        if latest_run is None
        else {
            "id": latest_run.id,
            "status": latest_run.status,
            "started_at": latest_run.started_at.isoformat() if latest_run.started_at else None,
            "finished_at": latest_run.finished_at.isoformat() if latest_run.finished_at else None,
            "rows_inserted": latest_run.rows_inserted,
        },
    }
