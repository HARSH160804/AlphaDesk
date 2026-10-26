"""Ingestion trigger + status endpoints."""
from __future__ import annotations

import json
import threading
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select

from app.db import SessionLocal
from app.models import IngestionRun
from app.schemas import IngestionStatus, IngestionTrigger
from app.services.scorecard import clear_cache


router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

# Single-flight lock so a second POST can't start while the first is running.
_ingest_lock = threading.Lock()


def _run_ingest() -> None:
    """Fire the pipeline. Imports inside the function so FastAPI startup stays light."""
    from ingestion.pipeline import ingest_universe

    try:
        ingest_universe()
    finally:
        clear_cache()
        _ingest_lock.release()


@router.post(
    "",
    response_model=IngestionTrigger,
    status_code=202,
    summary="Trigger an idempotent refresh of all NAVs + benchmarks",
)
def trigger_ingest(bg: BackgroundTasks) -> IngestionTrigger:
    if not _ingest_lock.acquire(blocking=False):
        raise HTTPException(409, "an ingestion is already running")
    bg.add_task(_run_ingest)
    return IngestionTrigger(
        accepted=True,
        message="ingestion scheduled; poll /api/ingest/status for progress",
        run_id=None,
    )


@router.get(
    "/status",
    response_model=IngestionStatus,
    summary="Latest ingestion run",
    responses={404: {"description": "No runs recorded yet"}},
)
def ingest_status() -> IngestionStatus:
    with SessionLocal() as s:
        run = s.scalars(
            select(IngestionRun).order_by(IngestionRun.id.desc()).limit(1)
        ).first()
    if run is None:
        raise HTTPException(404, "no ingestion runs recorded")
    errors = _parse_json_list(run.errors)
    warnings = _parse_json_list(run.warnings)
    return IngestionStatus(
        id=run.id,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        funds_processed=run.funds_processed or 0,
        benchmarks_processed=run.benchmarks_processed or 0,
        rows_inserted=run.rows_inserted or 0,
        errors=errors,
        warnings=warnings,
    )


def _parse_json_list(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except json.JSONDecodeError:
        pass
    return [raw]
