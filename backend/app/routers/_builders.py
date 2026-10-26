"""Shared conversion helpers between the metrics layer and Pydantic schemas."""
from __future__ import annotations

import math
from typing import Iterable

import pandas as pd

from analytics.metrics import FundScorecard, TRADING_DAYS_PER_YEAR
from app.models import Fund
from app.schemas import (
    DrawdownEpisode,
    DrawdownPoint,
    FundDetail,
    FundSummary,
    MetricPayload,
    NavPoint,
    RollingPoint,
    TrailingReturns,
)
from app.services.scorecard import (
    ScorecardBundle,
    drawdown_series,
    rolling_window_returns,
    worst_episode,
)


def summary_from_bundle(b: ScorecardBundle, *, pct_rank_3y: float | None = None) -> FundSummary:
    sc = b.scorecard
    return FundSummary(
        scheme_code=b.fund.scheme_code,
        name=b.fund.name,
        category=b.fund.category,
        amc=b.fund.amc,
        benchmark_id=b.fund.benchmark_id,
        as_of=sc.as_of,
        trailing=_trailing(sc),
        volatility=MetricPayload.from_metric(sc.volatility),
        max_drawdown=MetricPayload.from_metric(sc.max_drawdown),
        sharpe=MetricPayload.from_metric(sc.sharpe),
        sortino=MetricPayload.from_metric(sc.sortino),
        beta=MetricPayload.from_metric(sc.beta),
        alpha=MetricPayload.from_metric(sc.alpha),
        pct_rank_3y=pct_rank_3y,
    )


def detail_from_bundle(b: ScorecardBundle) -> FundDetail:
    sc = b.scorecard
    summary = summary_from_bundle(b)

    nav_series = _series_to_nav_points(b.nav)
    bench_series = _series_to_nav_points(b.bench) if b.bench is not None else []
    dd_series = _series_to_drawdown(drawdown_series(b.nav))

    rolling_1y = _rolling_frame(
        b.nav, b.bench, window=TRADING_DAYS_PER_YEAR
    )
    rolling_3y = _rolling_frame(
        b.nav, b.bench, window=3 * TRADING_DAYS_PER_YEAR
    )

    episode = worst_episode(b.nav)
    worst_dd = (
        DrawdownEpisode(
            peak_date=episode.peak_date,
            trough_date=episode.trough_date,
            recovery_date=episode.recovery_date,
            max_drawdown=episode.max_drawdown,
        )
        if episode is not None
        else None
    )

    return FundDetail(
        **summary.model_dump(by_alias=True),
        tracking_error=MetricPayload.from_metric(sc.tracking_error),
        information_ratio=MetricPayload.from_metric(sc.information_ratio),
        up_capture=MetricPayload.from_metric(sc.up_capture),
        down_capture=MetricPayload.from_metric(sc.down_capture),
        nav_series=nav_series,
        bench_series=bench_series,
        drawdown_series=dd_series,
        worst_drawdown=worst_dd,
        rolling_1y=rolling_1y,
        rolling_3y=rolling_3y,
    )


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _trailing(sc: FundScorecard) -> TrailingReturns:
    t = sc.trailing
    return TrailingReturns(
        **{
            "1M": MetricPayload.from_metric(t["1M"]),
            "3M": MetricPayload.from_metric(t["3M"]),
            "6M": MetricPayload.from_metric(t["6M"]),
            "1Y": MetricPayload.from_metric(t["1Y"]),
            "3Y": MetricPayload.from_metric(t["3Y"]),
            "5Y": MetricPayload.from_metric(t["5Y"]),
        }
    )


def _series_to_nav_points(s: pd.Series | None) -> list[NavPoint]:
    if s is None or s.empty:
        return []
    return [
        NavPoint(date=idx.date(), nav=float(val))
        for idx, val in s.items()
        if not math.isnan(float(val))
    ]


def _series_to_drawdown(s: pd.Series) -> list[DrawdownPoint]:
    if s.empty:
        return []
    return [
        DrawdownPoint(date=idx.date(), drawdown=float(val))
        for idx, val in s.items()
        if not math.isnan(float(val))
    ]


def _rolling_frame(nav: pd.Series, bench: pd.Series | None, *, window: int) -> list[RollingPoint]:
    fund_r = rolling_window_returns(nav, window)
    if fund_r.empty:
        return []
    bench_r = pd.Series(dtype=float)
    if bench is not None and not bench.empty:
        bench_r = rolling_window_returns(bench, window)
    out: list[RollingPoint] = []
    for idx, val in fund_r.items():
        b_val = None
        if not bench_r.empty and idx in bench_r.index:
            b_val = float(bench_r.loc[idx])
        out.append(RollingPoint(date=idx.date(), fund=float(val), bench=b_val))
    return out
