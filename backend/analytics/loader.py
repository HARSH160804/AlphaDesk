"""Load NAV / benchmark series from the DB into pandas."""
from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BenchmarkHistory, Fund, NavHistory


def load_fund_nav(session: Session, scheme_code: int, start: date | None = None) -> pd.Series:
    """Return a date-indexed NAV Series (ascending, strictly positive)."""
    stmt = select(NavHistory.date, NavHistory.nav).where(NavHistory.scheme_code == scheme_code)
    if start is not None:
        stmt = stmt.where(NavHistory.date >= start)
    stmt = stmt.order_by(NavHistory.date.asc())
    rows = session.execute(stmt).all()
    if not rows:
        return pd.Series(dtype=float)
    idx = pd.DatetimeIndex([r.date for r in rows])
    return pd.Series([float(r.nav) for r in rows], index=idx, name=f"scheme_{scheme_code}")


def load_benchmark(session: Session, benchmark_id: str, start: date | None = None) -> pd.Series:
    stmt = select(BenchmarkHistory.date, BenchmarkHistory.close).where(
        BenchmarkHistory.benchmark_id == benchmark_id
    )
    if start is not None:
        stmt = stmt.where(BenchmarkHistory.date >= start)
    stmt = stmt.order_by(BenchmarkHistory.date.asc())
    rows = session.execute(stmt).all()
    if not rows:
        return pd.Series(dtype=float)
    idx = pd.DatetimeIndex([r.date for r in rows])
    return pd.Series([float(r.close) for r in rows], index=idx, name=benchmark_id)


def load_fund_meta(session: Session, scheme_code: int) -> Fund | None:
    return session.get(Fund, scheme_code)
