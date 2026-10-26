"""Gather every piece of data a report needs, in one object.

Keeps the slide/section builders dumb: they consume `ReportContext`, never
touch the DB. One place to add a new field; one place to test the gather
step.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from analytics.loader import load_benchmark, load_fund_nav
from analytics.metrics import (
    DrawdownResult,
    FundScorecard,
    TRADING_DAYS_PER_YEAR,
    compute_scorecard,
    rolling_returns,
)
from app.config import get_settings
from app.models import Fund


@dataclass
class CalendarYear:
    year: int
    fund_return: float
    bench_return: Optional[float]

    @property
    def gap(self) -> Optional[float]:
        if self.bench_return is None:
            return None
        return self.fund_return - self.bench_return


@dataclass
class PeerRow:
    scheme_code: int
    name: str
    return_3y: float
    is_subject: bool = False


@dataclass
class ReportContext:
    fund: Fund
    period: str                           # "1Y" | "3Y" | "5Y" | "SI"
    as_of: date
    scorecard: FundScorecard

    # time-series restricted to the report period
    nav_series: pd.Series                 # date-indexed
    bench_series: Optional[pd.Series]
    drawdown_series: pd.Series            # peak-to-current nonpositive series
    rolling_1y: pd.DataFrame              # cols: fund, bench
    rolling_3y: pd.DataFrame
    worst_drawdown: Optional[DrawdownResult]

    # cross-sectional
    calendar_years: list[CalendarYear]
    peer_rank_3y: Optional[float]
    peer_leaderboard: list[PeerRow]

    # editorial
    takeaways: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(
        default_factory=lambda: [
            "Past performance does not guarantee future returns.",
            "Returns are gross of taxes; investor-level TDS and capital-gains tax apply.",
            "NAV data sourced from mfapi.in; benchmark data from Nifty via yfinance.",
            "Prepared for information only. Not a recommendation to buy or sell.",
        ]
    )

    @property
    def display_name(self) -> str:
        return self.fund.name.replace(" - Direct Plan - Growth Option", " - Direct Plan - Growth")


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------


def build_single_fund_context(
    session: Session,
    scheme_code: int,
    period: str = "3Y",
) -> ReportContext:
    fund = session.get(Fund, scheme_code)
    if fund is None:
        raise ValueError(f"fund {scheme_code} not found")

    nav_full = load_fund_nav(session, scheme_code)
    if nav_full.empty:
        raise ValueError(f"fund {scheme_code} has no NAV data")

    bench_full = None
    if fund.benchmark_id:
        bench_full = load_benchmark(session, fund.benchmark_id)
        if bench_full.empty:
            bench_full = None

    rf = get_settings().risk_free_rate
    scorecard = compute_scorecard(scheme_code, nav_full, bench_full, rf_annual=rf)

    end = pd.Timestamp(nav_full.index[-1])
    start = _period_start(end, period, nav_full.index[0])
    nav = nav_full.loc[start:end]
    bench = bench_full.loc[start:end] if bench_full is not None else None

    # Drawdown on the window
    dd = (nav / nav.cummax() - 1.0) if not nav.empty else pd.Series(dtype=float)

    r1y_fund = rolling_returns(nav_full, TRADING_DAYS_PER_YEAR).loc[start:end].rename("fund")
    r1y_bench = (
        rolling_returns(bench_full, TRADING_DAYS_PER_YEAR).loc[start:end].rename("bench")
        if bench_full is not None else pd.Series(dtype=float, name="bench")
    )
    r3y_fund = rolling_returns(nav_full, 3 * TRADING_DAYS_PER_YEAR).loc[start:end].rename("fund")
    r3y_bench = (
        rolling_returns(bench_full, 3 * TRADING_DAYS_PER_YEAR).loc[start:end].rename("bench")
        if bench_full is not None else pd.Series(dtype=float, name="bench")
    )

    rolling_1y = pd.concat([r1y_fund, r1y_bench], axis=1, sort=True).dropna(how="all")
    rolling_3y = pd.concat([r3y_fund, r3y_bench], axis=1, sort=True).dropna(how="all")

    worst = scorecard.max_drawdown
    worst_dd = None
    # scorecard.max_drawdown is a MetricValue (scalar); recompute the full DrawdownResult
    # on the window so slide 7 can show peak/trough/recovery dates.
    from analytics.metrics import max_drawdown as _max_drawdown
    if len(nav) >= 2:
        dd_full = _max_drawdown(nav)
        if isinstance(dd_full, DrawdownResult):
            worst_dd = dd_full
    _ = worst  # keep lint happy

    cal_years = _calendar_year_returns(nav_full, bench_full)
    peer_leaderboard, peer_rank = _peer_group(session, fund, scheme_code)
    takeaways = _derive_takeaways(scorecard, cal_years, peer_rank, worst_dd)

    return ReportContext(
        fund=fund,
        period=period,
        as_of=end.date(),
        scorecard=scorecard,
        nav_series=nav,
        bench_series=bench,
        drawdown_series=dd,
        rolling_1y=rolling_1y,
        rolling_3y=rolling_3y,
        worst_drawdown=worst_dd,
        calendar_years=cal_years,
        peer_rank_3y=peer_rank,
        peer_leaderboard=peer_leaderboard,
        takeaways=takeaways,
    )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _period_start(end: pd.Timestamp, period: str, series_start: pd.Timestamp) -> pd.Timestamp:
    period = period.upper()
    if period == "SI" or period == "ALL":
        return pd.Timestamp(series_start)
    years = {"1Y": 1, "3Y": 3, "5Y": 5}.get(period, 3)
    candidate = end - pd.DateOffset(years=years)
    if candidate < pd.Timestamp(series_start):
        return pd.Timestamp(series_start)
    return candidate


def _calendar_year_returns(
    nav: pd.Series, bench: Optional[pd.Series]
) -> list[CalendarYear]:
    out: list[CalendarYear] = []
    if nav.empty:
        return out
    years = sorted({int(d.year) for d in nav.index})
    end_year = pd.Timestamp.now().year
    for y in years:
        y_slice = nav[nav.index.year == y]
        if len(y_slice) < 2:
            continue
        f_ret = float(y_slice.iloc[-1] / y_slice.iloc[0] - 1.0)
        b_ret: Optional[float] = None
        if bench is not None:
            b_slice = bench[bench.index.year == y]
            if len(b_slice) >= 2:
                b_ret = float(b_slice.iloc[-1] / b_slice.iloc[0] - 1.0)
        # Flag partial current-year with YTD label; keep but mark via value
        _ = end_year  # not shown in the row today
        out.append(CalendarYear(year=y, fund_return=f_ret, bench_return=b_ret))
    return out


def _peer_group(session: Session, fund: Fund, subject_code: int) -> tuple[list[PeerRow], Optional[float]]:
    from sqlalchemy import select
    peers_q = session.scalars(
        select(Fund).where(Fund.category == fund.category).order_by(Fund.scheme_code)
    )
    peers = list(peers_q.all())
    scored: list[PeerRow] = []
    for p in peers:
        navp = load_fund_nav(session, p.scheme_code)
        if len(navp) < 2:
            continue
        end = pd.Timestamp(navp.index[-1])
        start = end - pd.DateOffset(years=3)
        start_val = _nav_on_or_before(navp, start)
        end_val = float(navp.iloc[-1])
        if start_val is None:
            continue
        years = (end - navp.index[navp.index <= start][-1]).days / 365.25
        if years <= 0:
            continue
        cagr = (end_val / start_val) ** (1 / years) - 1
        scored.append(
            PeerRow(
                scheme_code=p.scheme_code,
                name=p.name,
                return_3y=cagr,
                is_subject=p.scheme_code == subject_code,
            )
        )

    if not scored:
        return [], None
    scored.sort(key=lambda r: r.return_3y, reverse=True)
    rank = None
    for i, r in enumerate(scored):
        if r.is_subject:
            rank = (len(scored) - i) / len(scored) * 100.0
            break
    return scored, rank


def _nav_on_or_before(nav: pd.Series, target: pd.Timestamp) -> Optional[float]:
    sliced = nav.loc[nav.index <= target]
    return float(sliced.iloc[-1]) if not sliced.empty else None


# ---------------------------------------------------------------------------
# Editorial — three takeaways derived from the data
# ---------------------------------------------------------------------------


def _derive_takeaways(
    sc: FundScorecard,
    cal_years: list[CalendarYear],
    peer_rank_3y: Optional[float],
    worst_dd: Optional[DrawdownResult],
) -> list[str]:
    takeaways: list[str] = []

    # 1. Peer standing on 3Y CAGR
    y3 = sc.trailing.get("3Y")
    if y3 and y3.available:
        pct = y3.value * 100
        qualifier = ""
        if peer_rank_3y is not None:
            rank_label = _ordinal(peer_rank_3y)[0]
            if peer_rank_3y >= 75:
                qualifier = f", top quartile of its peer group ({rank_label} percentile)"
            elif peer_rank_3y >= 50:
                qualifier = f", above the peer median ({rank_label} percentile)"
            else:
                qualifier = f", below the peer median ({rank_label} percentile)"
        takeaways.append(f"3-year CAGR of {pct:.2f}%{qualifier}.")

    # 2. Risk profile — vol and max drawdown
    if sc.volatility.available and worst_dd is not None:
        takeaways.append(
            f"Annualised volatility of {sc.volatility.value * 100:.2f}% and a worst drawdown "
            f"of {worst_dd.max_drawdown * 100:.2f}% in {worst_dd.trough_date.strftime('%b %Y')}."
        )

    # 3. Benchmark-relative behaviour — how often it beat benchmark on calendar years
    beats = [c for c in cal_years if c.gap is not None and c.gap > 0]
    aligned = [c for c in cal_years if c.gap is not None]
    if aligned:
        takeaways.append(
            f"Beat benchmark in {len(beats)} of the last {len(aligned)} calendar years "
            f"(α ann. {sc.alpha.value * 100:+.2f}%)." if sc.alpha.available
            else f"Beat benchmark in {len(beats)} of the last {len(aligned)} calendar years."
        )

    return takeaways[:3]


def _ordinal(n: float) -> tuple[str, str]:
    n = int(round(n))
    suffix = "th"
    if n % 100 not in (11, 12, 13):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}", suffix


# Prevent linter warning on unused Path import
_ = Path, math
