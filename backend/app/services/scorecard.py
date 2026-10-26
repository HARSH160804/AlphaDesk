"""Scorecard loader with latest-nav-keyed caching.

Computing a full FundScorecard means loading 3,000+ NAV rows, aligning against
a benchmark, and running the whole metrics module. The result is a pure function
of (fund NAV series, bench series), so once we know the latest NAV date for a
fund we can cache the output. On a new ingest run that extends the series,
the cache key naturally invalidates.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from analytics.loader import load_benchmark, load_fund_nav
from analytics.metrics import (
    DrawdownResult,
    FundScorecard,
    compute_scorecard,
    max_drawdown,
    rolling_returns,
)
from app.config import get_settings
from app.db import SessionLocal
from app.models import BenchmarkHistory, Fund, NavHistory


_cache_lock = threading.Lock()
_scorecard_cache: dict[tuple[int, Optional[date], Optional[date]], FundScorecard] = {}
_nav_cache: dict[tuple[int, Optional[date]], pd.Series] = {}
_bench_cache: dict[tuple[str, Optional[date]], pd.Series] = {}


def _latest_nav_date(session: Session, scheme_code: int) -> Optional[date]:
    return session.scalar(
        select(func.max(NavHistory.date)).where(NavHistory.scheme_code == scheme_code)
    )


def _latest_bench_date(session: Session, benchmark_id: str) -> Optional[date]:
    return session.scalar(
        select(func.max(BenchmarkHistory.date)).where(
            BenchmarkHistory.benchmark_id == benchmark_id
        )
    )


def clear_cache() -> None:
    """Drop every cached series + scorecard. Called by the ingest endpoint."""
    with _cache_lock:
        _scorecard_cache.clear()
        _nav_cache.clear()
        _bench_cache.clear()


@dataclass(frozen=True)
class ScorecardBundle:
    fund: Fund
    nav: pd.Series
    bench: Optional[pd.Series]
    scorecard: FundScorecard


def get_bundle(session: Session, scheme_code: int) -> Optional[ScorecardBundle]:
    fund = session.get(Fund, scheme_code)
    if fund is None:
        return None

    nav_dt = _latest_nav_date(session, scheme_code)
    bench_dt = _latest_bench_date(session, fund.benchmark_id) if fund.benchmark_id else None
    key = (scheme_code, nav_dt, bench_dt)

    with _cache_lock:
        cached = _scorecard_cache.get(key)
    if cached is not None:
        nav = _nav_cache.get((scheme_code, nav_dt))
        bench = _bench_cache.get((fund.benchmark_id, bench_dt)) if fund.benchmark_id else None
        if nav is not None and (bench is not None or not fund.benchmark_id):
            return ScorecardBundle(fund=fund, nav=nav, bench=bench, scorecard=cached)

    # Compute fresh
    nav = load_fund_nav(session, scheme_code)
    bench: Optional[pd.Series] = None
    if fund.benchmark_id:
        bench = load_benchmark(session, fund.benchmark_id)
        if bench.empty:
            bench = None
    rf = get_settings().risk_free_rate
    sc = compute_scorecard(scheme_code, nav, bench, rf_annual=rf)

    with _cache_lock:
        _scorecard_cache[key] = sc
        _nav_cache[(scheme_code, nav_dt)] = nav
        if fund.benchmark_id and bench is not None:
            _bench_cache[(fund.benchmark_id, bench_dt)] = bench

    return ScorecardBundle(fund=fund, nav=nav, bench=bench, scorecard=sc)


def list_funds(session: Session) -> list[Fund]:
    return list(session.scalars(select(Fund).order_by(Fund.category, Fund.scheme_code)).all())


def drawdown_series(nav: pd.Series) -> pd.Series:
    """Running peak-to-current drawdown series (nonpositive, 0 at new highs)."""
    if nav.empty:
        return pd.Series(dtype=float)
    return nav / nav.cummax() - 1.0


def worst_episode(nav: pd.Series) -> Optional[DrawdownResult]:
    if nav.empty or len(nav) < 2:
        return None
    res = max_drawdown(nav)
    return res if isinstance(res, DrawdownResult) else None


def rolling_window_returns(nav: pd.Series, window_days: int) -> pd.Series:
    if nav.empty:
        return pd.Series(dtype=float)
    return rolling_returns(nav, window_days).dropna()
