"""FastAPI entry point. Endpoints are added in Phase 4; this stub exists so
`uvicorn app.main:app` works from day one.
"""
from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import func, select

from app.db import SessionLocal
from app.logging_setup import configure_logging
from app.models import Fund, IngestionRun, NavHistory
from app.sql_endpoint import router as sql_router

configure_logging()

app = FastAPI(
    title="AlphaDesk API",
    version="0.1.0",
    description="Mutual fund performance analytics and automated reporting.",
)

app.include_router(sql_router)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/stats", tags=["meta"])
def stats() -> dict:
    """Quick smoke check so the dashboard can show liveness."""
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
