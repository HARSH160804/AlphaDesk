"""`GET /api/sql/{query_name}` — run one of the whitelisted analyst queries.

The SQL files live under backend/sql/. Each file is readable on disk so an
analyst can audit the query without digging through code. The endpoint only
executes files it knows about (whitelist by filename) — no user-supplied SQL
is ever executed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.config import REPO_ROOT
from app.db import engine


SQL_DIR = REPO_ROOT / "backend" / "sql"

QUERIES: dict[str, str] = {
    "calendar_year_returns":      "01_calendar_year_returns.sql",
    "beats_benchmark_last_5y":    "02_beats_benchmark_last_5y.sql",
    "category_leaderboard_3y":    "03_category_leaderboard_3y.sql",
    "monthly_return_heatmap":     "04_monthly_return_heatmap.sql",
    "worst_drawdown_month_by_cat": "05_worst_drawdown_month_by_category.sql",
}


router = APIRouter(prefix="/api/sql", tags=["sql"])


def _load_sql(name: str) -> str:
    fname = QUERIES.get(name)
    if fname is None:
        raise HTTPException(status_code=404, detail=f"unknown query: {name}")
    path = SQL_DIR / fname
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"query file missing: {fname}")
    return path.read_text(encoding="utf-8")


@router.get("")
def list_queries() -> dict[str, Any]:
    return {"queries": sorted(QUERIES.keys())}


@router.get("/{query_name}")
def run_query(query_name: str) -> dict[str, Any]:
    sql = _load_sql(query_name)
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    # mappings() yields RowMapping; convert to plain dicts
    return {"query": query_name, "row_count": len(rows), "rows": [dict(r) for r in rows]}
