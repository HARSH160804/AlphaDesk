"""Performance and risk metrics for a NAV / price series.

Design
------
Every function accepts pandas Series indexed by date (sorted ascending,
strictly positive) and returns either a scalar :class:`MetricValue` or a
Series/DataFrame. When there is not enough history for a metric, the
function returns ``MetricValue.na(reason=...)``: it never silently
fabricates a value, and consumers can display the reason verbatim.

Conventions
-----------
* Trading days per year = 252.
* Daily simple returns, ``r_t = p_t / p_{t-1} - 1``.
* Sample standard deviation (ddof=1), matching pandas' default.
* CAGR = ``(end/start)^(1 / years) - 1`` where ``years = (end - start).days / 365.25``.
* The risk-free rate is annualised; a daily rate is derived as
  ``(1 + rf)^(1/252) - 1``.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date
from typing import Iterable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRADING_DAYS_PER_YEAR = 252


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricValue:
    """A metric result that may be unavailable, with a human-readable reason."""

    value: float
    reason: str | None = None

    @classmethod
    def ok(cls, value: float) -> "MetricValue":
        return cls(value=float(value), reason=None)

    @classmethod
    def na(cls, reason: str) -> "MetricValue":
        return cls(value=float("nan"), reason=reason)

    @property
    def available(self) -> bool:
        return not math.isnan(self.value)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        if self.available:
            return f"MetricValue({self.value:.6g})"
        return f"MetricValue(nan, reason={self.reason!r})"


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def daily_returns(nav: pd.Series) -> pd.Series:
    """Simple daily returns, dropping the first NaN."""
    _check_series(nav)
    return nav.pct_change().dropna()


def cagr(start: float, end: float, years: float) -> float:
    """Compound annual growth rate for a holding period expressed in years."""
    if years <= 0 or start <= 0 or end <= 0:
        return float("nan")
    return (end / start) ** (1.0 / years) - 1.0


def period_cagr(nav: pd.Series) -> MetricValue:
    """CAGR over the full span of the series."""
    _check_series(nav)
    if len(nav) < 2:
        return MetricValue.na("series has fewer than 2 points")
    start_date = nav.index[0]
    end_date = nav.index[-1]
    years = (end_date - start_date).days / 365.25
    if years <= 0:
        return MetricValue.na("series spans zero days")
    return MetricValue.ok(cagr(float(nav.iloc[0]), float(nav.iloc[-1]), years))


def _as_of_date(nav: pd.Series, as_of: pd.Timestamp | date | None) -> pd.Timestamp:
    if as_of is None:
        return pd.Timestamp(nav.index[-1])
    ts = pd.Timestamp(as_of)
    # snap to last available trading date on or before as_of
    idx = nav.index[nav.index <= ts]
    if len(idx) == 0:
        raise ValueError(f"no data on or before {ts.date()}")
    return pd.Timestamp(idx[-1])


def _nav_on_or_before(nav: pd.Series, target: pd.Timestamp) -> tuple[pd.Timestamp, float] | None:
    """Return (date, value) at the last observation ≤ target, or None."""
    sliced = nav.loc[nav.index <= target]
    if sliced.empty:
        return None
    return pd.Timestamp(sliced.index[-1]), float(sliced.iloc[-1])


# ---------------------------------------------------------------------------
# Trailing returns
# ---------------------------------------------------------------------------


def trailing_return(
    nav: pd.Series,
    months: int,
    *,
    as_of: pd.Timestamp | date | None = None,
    annualise_from_months: int = 12,
) -> MetricValue:
    """Trailing return over ``months`` calendar months.

    * For ``months < annualise_from_months`` the result is a *simple* return
      (end / start - 1).
    * For ``months >= annualise_from_months`` the result is annualised (CAGR).

    If there is no NAV available at or before ``as_of - months``, returns NaN.
    """
    _check_series(nav)
    if months <= 0:
        return MetricValue.na("months must be positive")
    end = _as_of_date(nav, as_of)
    start_target = end - pd.DateOffset(months=months)
    pair = _nav_on_or_before(nav, start_target)
    if pair is None:
        return MetricValue.na(f"insufficient history for {months}M trailing return")
    start_dt, start_val = pair
    end_val = float(nav.loc[end])
    if months < annualise_from_months:
        return MetricValue.ok(end_val / start_val - 1.0)
    years = (end - start_dt).days / 365.25
    return MetricValue.ok(cagr(start_val, end_val, years))


def trailing_returns_table(
    nav: pd.Series,
    *,
    months: Iterable[int] = (1, 3, 6, 12, 36, 60),
    as_of: pd.Timestamp | date | None = None,
) -> dict[str, MetricValue]:
    """Return a labelled dict ``{'1M': ..., '3M': ..., '1Y': ..., ...}``."""
    labels = {1: "1M", 3: "3M", 6: "6M", 12: "1Y", 36: "3Y", 60: "5Y"}
    out: dict[str, MetricValue] = {}
    for m in months:
        key = labels.get(m, f"{m}M")
        out[key] = trailing_return(nav, m, as_of=as_of)
    return out


# ---------------------------------------------------------------------------
# Rolling returns
# ---------------------------------------------------------------------------


def rolling_returns(nav: pd.Series, window_trading_days: int) -> pd.Series:
    """Rolling window return series. ``r_t = p_t / p_{t-window} - 1``."""
    _check_series(nav)
    if window_trading_days <= 0:
        raise ValueError("window_trading_days must be positive")
    return (nav / nav.shift(window_trading_days)) - 1.0


def pct_beat_benchmark(
    fund_nav: pd.Series,
    bench: pd.Series,
    window_trading_days: int,
) -> MetricValue:
    """Share of rolling periods where the fund's rolling return > benchmark's."""
    aligned = _align_series(fund_nav, bench)
    f_r = rolling_returns(aligned["fund"], window_trading_days).dropna()
    b_r = rolling_returns(aligned["bench"], window_trading_days).dropna()
    joined = pd.concat({"f": f_r, "b": b_r}, axis=1).dropna()
    if joined.empty:
        return MetricValue.na("no overlapping rolling periods")
    return MetricValue.ok(float((joined["f"] > joined["b"]).mean()))


# ---------------------------------------------------------------------------
# Volatility, Sharpe, Sortino
# ---------------------------------------------------------------------------


def annualized_volatility(nav: pd.Series) -> MetricValue:
    """Annualised volatility = ``std(daily_returns) * sqrt(252)`` (ddof=1)."""
    _check_series(nav)
    r = daily_returns(nav)
    if len(r) < 2:
        return MetricValue.na("fewer than 2 daily returns")
    return MetricValue.ok(float(r.std(ddof=1)) * math.sqrt(TRADING_DAYS_PER_YEAR))


def _daily_rf(annual_rf: float) -> float:
    return (1.0 + annual_rf) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0


def sharpe_ratio(nav: pd.Series, rf_annual: float = 0.065) -> MetricValue:
    """Sharpe = (mean(excess_daily_returns) / std(excess_daily_returns)) * sqrt(252)."""
    _check_series(nav)
    r = daily_returns(nav)
    if len(r) < 2:
        return MetricValue.na("fewer than 2 daily returns")
    excess = r - _daily_rf(rf_annual)
    sd = float(excess.std(ddof=1))
    if sd == 0:
        return MetricValue.na("zero volatility")
    return MetricValue.ok(float(excess.mean()) / sd * math.sqrt(TRADING_DAYS_PER_YEAR))


def sortino_ratio(nav: pd.Series, rf_annual: float = 0.065) -> MetricValue:
    """Sortino uses downside deviation (returns below the daily rf) in place of std."""
    _check_series(nav)
    r = daily_returns(nav)
    if len(r) < 2:
        return MetricValue.na("fewer than 2 daily returns")
    daily_rf = _daily_rf(rf_annual)
    excess = r - daily_rf
    downside = excess[excess < 0]
    if downside.empty:
        return MetricValue.na("no downside observations")
    # Downside deviation is the RMS of negative excess returns (standard Sortino definition).
    dd = math.sqrt(float((downside ** 2).mean()))
    if dd == 0:
        return MetricValue.na("zero downside deviation")
    return MetricValue.ok(float(excess.mean()) / dd * math.sqrt(TRADING_DAYS_PER_YEAR))


# ---------------------------------------------------------------------------
# Drawdown
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DrawdownResult:
    max_drawdown: float  # negative, e.g. -0.23 for -23 %
    peak_date: date
    trough_date: date
    recovery_date: date | None  # None if never recovered within the series


def max_drawdown(nav: pd.Series) -> DrawdownResult | MetricValue:
    """Largest peak-to-trough decline on the series.

    ``drawdown_t = p_t / running_max(p)_t - 1`` (nonpositive).
    Peak date is where the running max was last set before the trough.
    Recovery date is the first date after the trough where NAV returns to the peak.
    """
    _check_series(nav)
    if len(nav) < 2:
        return MetricValue.na("fewer than 2 points")
    running_max = nav.cummax()
    dd = nav / running_max - 1.0
    trough_pos = int(dd.values.argmin())
    max_dd = float(dd.iloc[trough_pos])
    if max_dd == 0:
        return DrawdownResult(0.0, nav.index[0].date(), nav.index[0].date(), nav.index[0].date())
    peak_value = float(running_max.iloc[trough_pos])
    # Peak date: last date on or before the trough where NAV equalled the running max.
    pre = nav.iloc[: trough_pos + 1]
    peak_idx = int(np.where(pre.values >= peak_value)[0][-1])
    peak_date = pre.index[peak_idx].date()
    trough_date = nav.index[trough_pos].date()
    # Recovery: first date after trough where NAV >= peak_value.
    post = nav.iloc[trough_pos + 1 :]
    rec_mask = post.values >= peak_value
    recovery_date = post.index[int(np.where(rec_mask)[0][0])].date() if rec_mask.any() else None
    return DrawdownResult(
        max_drawdown=max_dd,
        peak_date=peak_date,
        trough_date=trough_date,
        recovery_date=recovery_date,
    )


# ---------------------------------------------------------------------------
# Benchmark-relative metrics
# ---------------------------------------------------------------------------


def _align_series(fund_nav: pd.Series, bench: pd.Series) -> pd.DataFrame:
    """Inner-join two series on their shared trading dates."""
    _check_series(fund_nav)
    _check_series(bench)
    df = pd.concat({"fund": fund_nav, "bench": bench}, axis=1, sort=True).dropna()
    return df


def beta(fund_nav: pd.Series, bench: pd.Series) -> MetricValue:
    """Beta = cov(fund_r, bench_r) / var(bench_r), both daily, ddof=1."""
    aligned = _align_series(fund_nav, bench)
    f = aligned["fund"].pct_change().dropna()
    b = aligned["bench"].pct_change().dropna()
    joined = pd.concat({"f": f, "b": b}, axis=1).dropna()
    if len(joined) < 2:
        return MetricValue.na("fewer than 2 aligned returns")
    var_b = float(joined["b"].var(ddof=1))
    if var_b == 0:
        return MetricValue.na("benchmark variance is zero")
    cov = float(joined.cov(ddof=1).loc["f", "b"])
    return MetricValue.ok(cov / var_b)


def jensens_alpha(
    fund_nav: pd.Series,
    bench: pd.Series,
    rf_annual: float = 0.065,
) -> MetricValue:
    """Jensen's alpha, annualised.

    ``α = R_f,ann - [ rf + β · (R_b,ann - rf) ]``
    where returns are the CAGR over the overlapping sample.
    """
    aligned = _align_series(fund_nav, bench)
    if len(aligned) < 2:
        return MetricValue.na("fewer than 2 aligned observations")
    years = (aligned.index[-1] - aligned.index[0]).days / 365.25
    if years <= 0:
        return MetricValue.na("aligned sample spans zero days")
    r_f = cagr(float(aligned["fund"].iloc[0]), float(aligned["fund"].iloc[-1]), years)
    r_b = cagr(float(aligned["bench"].iloc[0]), float(aligned["bench"].iloc[-1]), years)
    b = beta(fund_nav, bench)
    if not b.available:
        return MetricValue.na(b.reason or "beta unavailable")
    expected = rf_annual + b.value * (r_b - rf_annual)
    return MetricValue.ok(r_f - expected)


def tracking_error(fund_nav: pd.Series, bench: pd.Series) -> MetricValue:
    """Annualised standard deviation of the daily fund-minus-benchmark return."""
    aligned = _align_series(fund_nav, bench)
    diff = aligned["fund"].pct_change() - aligned["bench"].pct_change()
    diff = diff.dropna()
    if len(diff) < 2:
        return MetricValue.na("fewer than 2 aligned return diffs")
    return MetricValue.ok(float(diff.std(ddof=1)) * math.sqrt(TRADING_DAYS_PER_YEAR))


def information_ratio(fund_nav: pd.Series, bench: pd.Series) -> MetricValue:
    """IR = (annualised excess return over benchmark) / tracking_error."""
    aligned = _align_series(fund_nav, bench)
    if len(aligned) < 2:
        return MetricValue.na("fewer than 2 aligned observations")
    years = (aligned.index[-1] - aligned.index[0]).days / 365.25
    if years <= 0:
        return MetricValue.na("aligned sample spans zero days")
    r_f = cagr(float(aligned["fund"].iloc[0]), float(aligned["fund"].iloc[-1]), years)
    r_b = cagr(float(aligned["bench"].iloc[0]), float(aligned["bench"].iloc[-1]), years)
    te = tracking_error(fund_nav, bench)
    if not te.available or te.value == 0:
        return MetricValue.na(te.reason or "zero tracking error")
    return MetricValue.ok((r_f - r_b) / te.value)


def capture_ratios(fund_nav: pd.Series, bench: pd.Series) -> tuple[MetricValue, MetricValue]:
    """Up- and down-capture.

    Up-capture = compound fund return on days the bench rose, divided by
    the benchmark's compound return on the same days. Down-capture is the
    mirror calculation on days the bench fell. Returned as (up, down).
    """
    aligned = _align_series(fund_nav, bench)
    f = aligned["fund"].pct_change()
    b = aligned["bench"].pct_change()
    joined = pd.concat({"f": f, "b": b}, axis=1).dropna()
    if joined.empty:
        return MetricValue.na("no aligned returns"), MetricValue.na("no aligned returns")

    def _capture(mask: pd.Series) -> MetricValue:
        sub = joined.loc[mask]
        if sub.empty:
            return MetricValue.na("no observations on that side")
        bench_cum = float((1.0 + sub["b"]).prod() - 1.0)
        fund_cum = float((1.0 + sub["f"]).prod() - 1.0)
        if bench_cum == 0:
            return MetricValue.na("benchmark cumulative return is zero")
        return MetricValue.ok(fund_cum / bench_cum)

    return _capture(joined["b"] > 0), _capture(joined["b"] < 0)


# ---------------------------------------------------------------------------
# Composite scorecard
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FundScorecard:
    scheme_code: int
    as_of: date
    trailing: dict[str, MetricValue]
    volatility: MetricValue
    sharpe: MetricValue
    sortino: MetricValue
    max_drawdown: MetricValue
    beta: MetricValue
    alpha: MetricValue
    tracking_error: MetricValue
    information_ratio: MetricValue
    up_capture: MetricValue
    down_capture: MetricValue
    pct_beat_1y: MetricValue
    pct_beat_3y: MetricValue


def compute_scorecard(
    scheme_code: int,
    fund_nav: pd.Series,
    bench: pd.Series | None,
    rf_annual: float = 0.065,
    as_of: pd.Timestamp | date | None = None,
) -> FundScorecard:
    """Compute every scalar metric for a fund in one call."""
    _check_series(fund_nav)
    end = _as_of_date(fund_nav, as_of)
    trailing = trailing_returns_table(fund_nav, as_of=end)
    vol = annualized_volatility(fund_nav)
    sh = sharpe_ratio(fund_nav, rf_annual)
    so = sortino_ratio(fund_nav, rf_annual)
    dd_full = max_drawdown(fund_nav)
    dd_val = (
        MetricValue.ok(dd_full.max_drawdown) if isinstance(dd_full, DrawdownResult) else dd_full
    )

    if bench is None or bench.empty:
        na = MetricValue.na("no benchmark data")
        return FundScorecard(
            scheme_code=scheme_code,
            as_of=end.date(),
            trailing=trailing,
            volatility=vol,
            sharpe=sh,
            sortino=so,
            max_drawdown=dd_val,
            beta=na,
            alpha=na,
            tracking_error=na,
            information_ratio=na,
            up_capture=na,
            down_capture=na,
            pct_beat_1y=na,
            pct_beat_3y=na,
        )
    b = beta(fund_nav, bench)
    a = jensens_alpha(fund_nav, bench, rf_annual)
    te = tracking_error(fund_nav, bench)
    ir = information_ratio(fund_nav, bench)
    up, dn = capture_ratios(fund_nav, bench)
    beat_1y = pct_beat_benchmark(fund_nav, bench, TRADING_DAYS_PER_YEAR)
    beat_3y = pct_beat_benchmark(fund_nav, bench, 3 * TRADING_DAYS_PER_YEAR)

    return FundScorecard(
        scheme_code=scheme_code,
        as_of=end.date(),
        trailing=trailing,
        volatility=vol,
        sharpe=sh,
        sortino=so,
        max_drawdown=dd_val,
        beta=b,
        alpha=a,
        tracking_error=te,
        information_ratio=ir,
        up_capture=up,
        down_capture=dn,
        pct_beat_1y=beat_1y,
        pct_beat_3y=beat_3y,
    )


# ---------------------------------------------------------------------------
# Category percentile rank
# ---------------------------------------------------------------------------


def category_percentile_rank(
    df: pd.DataFrame,
    *,
    category_col: str,
    metric_col: str,
    higher_is_better: bool = True,
) -> pd.Series:
    """Percentile rank within each category.

    Returns a Series aligned to ``df.index`` with values in [0, 100]:
    0 means worst in the peer group, 100 best. NaN metric values stay NaN.
    """
    if higher_is_better:
        ranks = df.groupby(category_col)[metric_col].rank(pct=True)
    else:
        ranks = df.groupby(category_col)[metric_col].rank(pct=True, ascending=False)
    return (ranks * 100.0).astype(float)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _check_series(s: pd.Series) -> None:
    if not isinstance(s, pd.Series):
        raise TypeError("expected a pandas Series")
    if s.empty:
        return
    if not isinstance(s.index, pd.DatetimeIndex):
        raise TypeError("series index must be a DatetimeIndex")
    if not s.index.is_monotonic_increasing:
        raise ValueError("series index must be sorted ascending")
    if (s <= 0).any():
        raise ValueError("series must be strictly positive")
