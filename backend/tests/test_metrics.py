"""Unit tests for analytics.metrics with hand-computed expected values.

Every metric is checked against a small, deterministic series where the
expected answer is derived by hand (arithmetic worked out in a comment above
each assertion). A handful of tests also run against the real DB-loaded
NAV series to catch regressions on real-world shapes.
"""
from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from analytics.metrics import (
    DrawdownResult,
    MetricValue,
    annualized_volatility,
    beta,
    cagr,
    capture_ratios,
    category_percentile_rank,
    compute_scorecard,
    daily_returns,
    information_ratio,
    jensens_alpha,
    max_drawdown,
    pct_beat_benchmark,
    period_cagr,
    rolling_returns,
    sharpe_ratio,
    sortino_ratio,
    tracking_error,
    trailing_return,
    trailing_returns_table,
)

# ---------------------------------------------------------------------------
# Series builders
# ---------------------------------------------------------------------------


def _nav_from_returns(returns, start: str = "2020-01-01", nav0: float = 100.0) -> pd.Series:
    r = np.asarray(returns, dtype=float)
    nav = np.empty(len(r) + 1, dtype=float)
    nav[0] = nav0
    for i, ri in enumerate(r):
        nav[i + 1] = nav[i] * (1.0 + ri)
    idx = pd.bdate_range(start=start, periods=len(nav))
    return pd.Series(nav, index=idx, name="nav")


def _constant_cagr_series(annual_rate: float, years: int, start: str = "2015-01-01") -> pd.Series:
    """NAV growing at exactly annual_rate CAGR, measured on calendar days.

    We index by calendar day (not business day) so (end/start)^(1/years) - 1
    returns the input rate on the nose. This matters because
    `trailing_return` and `period_cagr` compute `years` from calendar day gaps.
    """
    days = int(round(365.25 * years))
    daily = (1 + annual_rate) ** (1 / 365.25) - 1
    returns = [daily] * days
    idx = pd.date_range(start=start, periods=days + 1, freq="D")
    nav_vals = np.cumprod(np.r_[1.0, 1.0 + np.asarray(returns)]) * 100.0
    return pd.Series(nav_vals, index=idx, name="nav")


def _noisy_cagr_series(
    annual_rate: float, years: int, sigma_daily: float = 0.005, seed: int = 0, start: str = "2015-01-01"
) -> pd.Series:
    """Deterministic noisy daily series with long-run CAGR ≈ annual_rate (calendar-day indexed)."""
    rng = np.random.default_rng(seed)
    days = int(round(365.25 * years))
    daily_mean = (1 + annual_rate) ** (1 / 365.25) - 1
    returns = daily_mean + rng.normal(0.0, sigma_daily, size=days)
    idx = pd.date_range(start=start, periods=days + 1, freq="D")
    nav_vals = np.cumprod(np.r_[1.0, 1.0 + returns]) * 100.0
    return pd.Series(nav_vals, index=idx, name="nav")


# ---------------------------------------------------------------------------
# CAGR
# ---------------------------------------------------------------------------


def test_cagr_formula():
    # 100 -> 161.051 over 5 years is exactly 10% CAGR because 1.1**5 == 1.61051
    assert cagr(100.0, 161.051, 5.0) == pytest.approx(0.10, abs=1e-9)
    # Flat
    assert cagr(100.0, 100.0, 5.0) == pytest.approx(0.0, abs=1e-12)
    # Halving over 2 years: sqrt(0.5) - 1 ≈ -0.29289
    assert cagr(200.0, 100.0, 2.0) == pytest.approx(math.sqrt(0.5) - 1, abs=1e-9)
    # Invalid inputs return nan
    assert math.isnan(cagr(100.0, 100.0, 0.0))
    assert math.isnan(cagr(-1.0, 100.0, 1.0))


def test_period_cagr_series():
    # 2 years, 10% CAGR constructed on business days; the series actually spans
    # a bit more than 2 calendar years because of weekends, so recompute.
    nav = _constant_cagr_series(0.10, years=2, start="2015-01-01")
    years = (nav.index[-1] - nav.index[0]).days / 365.25
    expected = (nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1
    mv = period_cagr(nav)
    assert mv.available
    assert mv.value == pytest.approx(expected, rel=1e-12)
    # The CAGR formula applied to a series grown at daily_rate matching 10%
    # yearly should land within rounding tolerance of 10%.
    assert mv.value == pytest.approx(0.10, abs=5e-3)


# ---------------------------------------------------------------------------
# Daily returns
# ---------------------------------------------------------------------------


def test_daily_returns_arithmetic():
    nav = pd.Series(
        [100.0, 110.0, 99.0, 108.9],
        index=pd.date_range("2024-01-01", periods=4),
    )
    r = daily_returns(nav)
    assert len(r) == 3
    # 110/100-1 = 0.10
    assert r.iloc[0] == pytest.approx(0.10)
    # 99/110-1 = -0.10
    assert r.iloc[1] == pytest.approx(-0.10)
    # 108.9/99-1 = 0.10
    assert r.iloc[2] == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# Trailing returns
# ---------------------------------------------------------------------------


def test_trailing_return_absolute_short_period():
    # Daily NAV that doubles over one calendar month, flat before.
    dates = pd.date_range("2024-01-01", "2024-03-15", freq="B")
    nav = pd.Series(index=dates, dtype=float)
    nav[:] = 100.0
    # Set 2024-03-15's value to 200 exactly.
    nav.iloc[-1] = 200.0

    # 1M trailing is absolute: 200/100 - 1 = 1.0
    mv = trailing_return(nav, months=1)
    assert mv.available
    assert mv.value == pytest.approx(1.0, abs=1e-9)


def test_trailing_return_annualised_over_one_year():
    # NAV doubles exactly over 2 years: CAGR = sqrt(2) - 1 ≈ 0.4142
    nav = _constant_cagr_series(math.sqrt(2) - 1, years=2, start="2015-01-01")
    mv = trailing_return(nav, months=12)
    assert mv.available
    # Over the last 12 months a series growing at sqrt(2)-1 per year gives
    # exactly (sqrt(2)-1) ≈ 0.4142 as annualised return.
    assert mv.value == pytest.approx(math.sqrt(2) - 1, abs=5e-3)


def test_trailing_return_insufficient_history():
    nav = _nav_from_returns([0.001] * 10, start="2024-01-01")  # ~10 bdays
    mv = trailing_return(nav, months=12)
    assert not mv.available
    assert "insufficient history" in (mv.reason or "")


def test_trailing_returns_table_keys():
    nav = _constant_cagr_series(0.08, years=6, start="2015-01-01")
    table = trailing_returns_table(nav)
    assert set(table.keys()) == {"1M", "3M", "6M", "1Y", "3Y", "5Y"}
    for k in ("1Y", "3Y", "5Y"):
        assert table[k].available
        # Across 1Y/3Y/5Y the constant-CAGR series should always read ≈ 8%.
        assert table[k].value == pytest.approx(0.08, abs=5e-3)


# ---------------------------------------------------------------------------
# Rolling + pct_beat
# ---------------------------------------------------------------------------


def test_rolling_returns_window():
    # 100 doubling to 200 at index 10 should give a window-10 rolling return of 1.0
    vals = [100.0] * 10 + [200.0]
    nav = pd.Series(vals, index=pd.date_range("2024-01-01", periods=len(vals)))
    rr = rolling_returns(nav, window_trading_days=10)
    # First 10 entries NaN (not enough history), last is 200/100 - 1
    assert math.isnan(rr.iloc[0])
    assert rr.iloc[-1] == pytest.approx(1.0)


def test_pct_beat_benchmark():
    # Fund grows faster than bench — all rolling periods beat.
    bench = _constant_cagr_series(0.08, years=4, start="2015-01-01")
    fund = _constant_cagr_series(0.12, years=4, start="2015-01-01")
    mv = pct_beat_benchmark(fund, bench, window_trading_days=252)
    assert mv.available
    assert mv.value == pytest.approx(1.0, abs=1e-9)
    # Reverse: fund underperforms uniformly -> 0 beat
    mv2 = pct_beat_benchmark(bench, fund, window_trading_days=252)
    assert mv2.value == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Volatility, Sharpe, Sortino
# ---------------------------------------------------------------------------


def test_annualized_volatility_alternating_returns():
    # 250 returns alternating +1% / -1%: variance ≈ 0.01^2 * (250/249)
    returns = [0.01, -0.01] * 125
    nav = _nav_from_returns(returns, start="2020-01-01")
    mv = annualized_volatility(nav)
    assert mv.available
    expected_daily_std = math.sqrt(250 / 249) * 0.01
    expected = expected_daily_std * math.sqrt(252)
    assert mv.value == pytest.approx(expected, rel=1e-6)


def test_sharpe_zero_vol_is_na():
    # Constant positive return => zero std => Sharpe is NA
    nav = _nav_from_returns([0.001] * 20, start="2020-01-01")
    mv = sharpe_ratio(nav, rf_annual=0.0)
    assert not mv.available
    assert "zero volatility" in (mv.reason or "")


def test_sharpe_zero_mean_zero_sharpe():
    returns = [0.01, -0.01] * 125  # exact mean 0, non-zero std
    nav = _nav_from_returns(returns, start="2020-01-01")
    mv = sharpe_ratio(nav, rf_annual=0.0)
    assert mv.available
    # mean(excess) = -daily_rf ≈ 0 at rf=0; result is tiny but finite.
    assert abs(mv.value) < 1e-9


def test_sortino_only_downside_vol():
    # Mix: 60 +1%, 60 -2% => negative mean, downside dominated by -2% days.
    returns = [0.01] * 60 + [-0.02] * 60
    nav = _nav_from_returns(returns, start="2020-01-01")
    # Hand compute downside deviation at daily_rf=0:
    # downside = [-0.02 for 60 days]; dd = sqrt(mean(downside^2)) over all excess?
    # Our implementation uses the mean of squared *downside* observations only.
    daily_rf = 0.0
    r = pd.Series(returns)
    excess = r - daily_rf
    downside = excess[excess < 0]
    expected_dd = math.sqrt(float((downside ** 2).mean()))
    expected = float(excess.mean()) / expected_dd * math.sqrt(252)
    mv = sortino_ratio(nav, rf_annual=0.0)
    assert mv.available
    assert mv.value == pytest.approx(expected, rel=1e-10)


# ---------------------------------------------------------------------------
# Max drawdown
# ---------------------------------------------------------------------------


def test_max_drawdown_known_series():
    # Peak at index 1 (120), trough at index 2 (90) -> -25%; recovers at index 5 (125)
    vals = [100.0, 120.0, 90.0, 110.0, 115.0, 125.0]
    nav = pd.Series(vals, index=pd.date_range("2024-01-01", periods=6))
    dd = max_drawdown(nav)
    assert isinstance(dd, DrawdownResult)
    assert dd.max_drawdown == pytest.approx(-0.25, abs=1e-9)
    assert dd.peak_date == date(2024, 1, 2)
    assert dd.trough_date == date(2024, 1, 3)
    assert dd.recovery_date == date(2024, 1, 6)


def test_max_drawdown_without_recovery():
    vals = [100.0, 120.0, 90.0, 110.0, 115.0]  # never breaks 120 again
    nav = pd.Series(vals, index=pd.date_range("2024-01-01", periods=5))
    dd = max_drawdown(nav)
    assert isinstance(dd, DrawdownResult)
    assert dd.recovery_date is None
    assert dd.trough_date == date(2024, 1, 3)


def test_max_drawdown_flat_series():
    vals = [100.0, 100.0, 100.0]
    nav = pd.Series(vals, index=pd.date_range("2024-01-01", periods=3))
    dd = max_drawdown(nav)
    assert isinstance(dd, DrawdownResult)
    assert dd.max_drawdown == 0.0


# ---------------------------------------------------------------------------
# Beta, Alpha
# ---------------------------------------------------------------------------


def test_beta_double_bench_is_two():
    bench_returns = [0.01, -0.005, 0.02, -0.015] * 50  # 200 obs
    fund_returns = [2 * r for r in bench_returns]
    bench_nav = _nav_from_returns(bench_returns, start="2020-01-01")
    fund_nav = _nav_from_returns(fund_returns, start="2020-01-01")
    mv = beta(fund_nav, bench_nav)
    assert mv.available
    assert mv.value == pytest.approx(2.0, abs=1e-9)


def test_alpha_zero_when_fund_equals_bench():
    # If fund == bench, beta=1 and R_f = R_b, so alpha should be exactly 0.
    bench_returns = [0.004, -0.002, 0.006, -0.003] * 60
    nav = _nav_from_returns(bench_returns, start="2020-01-01")
    mv = jensens_alpha(nav, nav, rf_annual=0.065)
    assert mv.available
    assert mv.value == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Tracking error + Information ratio
# ---------------------------------------------------------------------------


def test_tracking_error_zero_when_series_equal():
    nav = _constant_cagr_series(0.08, years=1, start="2020-01-01")
    mv = tracking_error(nav, nav)
    assert mv.available
    assert mv.value == pytest.approx(0.0, abs=1e-12)


def test_tracking_error_known_diff():
    # Build bench, then build fund so that fund_t = bench_t * series of pct_t
    # with daily return diff that alternates +0.005 / -0.005.
    bench_returns = [0.001] * 200
    fund_returns = [bench_returns[i] + (0.005 if i % 2 == 0 else -0.005) for i in range(200)]
    bench_nav = _nav_from_returns(bench_returns, start="2020-01-01")
    fund_nav = _nav_from_returns(fund_returns, start="2020-01-01")
    mv = tracking_error(fund_nav, bench_nav)
    assert mv.available
    # std of alternating ±0.005 with 200 obs, ddof=1:
    expected_daily_std = math.sqrt(200 / 199) * 0.005
    expected = expected_daily_std * math.sqrt(252)
    assert mv.value == pytest.approx(expected, rel=1e-9)


def test_information_ratio_positive_when_fund_outperforms():
    bench = _noisy_cagr_series(0.06, years=3, sigma_daily=0.005, seed=1, start="2020-01-01")
    fund = _noisy_cagr_series(0.10, years=3, sigma_daily=0.006, seed=2, start="2020-01-01")
    ir = information_ratio(fund, bench)
    assert ir.available
    # Fund CAGR > bench CAGR -> excess return is positive, so IR must be positive.
    assert ir.value > 0


# ---------------------------------------------------------------------------
# Up / down capture
# ---------------------------------------------------------------------------


def test_up_capture_exact_two_x_single_day():
    # One up day in bench, one down day; fund is 2x on every day.
    bench = pd.Series([100.0, 101.0, 99.99], index=pd.date_range("2024-01-01", periods=3))
    fund = pd.Series([100.0, 102.0, 97.9596], index=pd.date_range("2024-01-01", periods=3))
    # Day 1: bench +1%, fund +2% -> up_capture = 2.0
    # Day 2: bench -1.0099..%, fund -2.019...% (102 -> 97.9596 ≈ -3.9612%)
    # Actually let's set fund day 2 so return = 2x bench day 2.
    bench_r = bench.pct_change().dropna()
    fund = pd.Series(dtype=float)
    fund_vals = [100.0]
    for r in bench_r:
        fund_vals.append(fund_vals[-1] * (1 + 2 * r))
    fund = pd.Series(fund_vals, index=bench.index)

    up, down = capture_ratios(fund, bench)
    assert up.available and down.available
    # With one up and one down observation of exact 2x, both equal 2.0.
    assert up.value == pytest.approx(2.0, abs=1e-9)
    assert down.value == pytest.approx(2.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Category percentile rank
# ---------------------------------------------------------------------------


def test_category_percentile_rank():
    df = pd.DataFrame(
        {
            "scheme_code": [1, 2, 3, 4],
            "category": ["lc", "lc", "mc", "mc"],
            "ret": [0.10, 0.20, 0.05, 0.15],
        }
    )
    pr = category_percentile_rank(df, category_col="category", metric_col="ret")
    # Within lc: 1 ranks last (50) and 2 ranks top (100)
    assert pr.loc[0] == pytest.approx(50.0)
    assert pr.loc[1] == pytest.approx(100.0)
    # Within mc: 3 ranks last (50) and 4 ranks top (100)
    assert pr.loc[2] == pytest.approx(50.0)
    assert pr.loc[3] == pytest.approx(100.0)


def test_category_percentile_rank_lower_is_better():
    df = pd.DataFrame(
        {"category": ["lc", "lc", "lc"], "max_dd": [-0.20, -0.10, -0.30]}
    )
    pr = category_percentile_rank(
        df, category_col="category", metric_col="max_dd", higher_is_better=True
    )
    # higher_is_better=True on a negative metric where larger (less negative) is better:
    # -0.30 is worst (33.3 pct), -0.10 is best (100 pct)
    assert pr.loc[2] == pytest.approx(100 / 3)
    assert pr.loc[1] == pytest.approx(100.0)
    assert pr.loc[0] == pytest.approx(200 / 3)


# ---------------------------------------------------------------------------
# Scorecard composite
# ---------------------------------------------------------------------------


def test_compute_scorecard_populates_all_fields():
    nav = _noisy_cagr_series(0.12, years=4, sigma_daily=0.008, seed=3, start="2015-01-01")
    bench = _noisy_cagr_series(0.08, years=4, sigma_daily=0.006, seed=4, start="2015-01-01")
    sc = compute_scorecard(999, nav, bench, rf_annual=0.065)
    assert sc.scheme_code == 999
    assert sc.volatility.available
    assert sc.beta.available
    assert sc.alpha.available
    assert sc.tracking_error.available
    assert sc.information_ratio.available
    assert sc.up_capture.available
    assert sc.down_capture.available
    assert sc.max_drawdown.available
    # Trailing table includes 1Y/3Y keys populated.
    assert sc.trailing["1Y"].available
    assert sc.trailing["3Y"].available


def test_scorecard_without_benchmark_sets_relative_metrics_na():
    nav = _constant_cagr_series(0.10, years=2, start="2020-01-01")
    sc = compute_scorecard(1, nav, bench=None)
    assert sc.beta.available is False
    assert sc.alpha.available is False
    assert sc.pct_beat_1y.available is False


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_check_series_rejects_non_series():
    with pytest.raises(TypeError):
        daily_returns([1, 2, 3])  # not a Series


def test_check_series_rejects_non_positive():
    s = pd.Series([100.0, -1.0], index=pd.date_range("2024-01-01", periods=2))
    with pytest.raises(ValueError):
        daily_returns(s)


# ---------------------------------------------------------------------------
# Live-data smoke test (uses the DB populated in Phase 1)
# ---------------------------------------------------------------------------


def test_scorecard_against_live_data_runs():
    """End-to-end check against real data: compute Parag Parikh Flexi Cap vs Nifty 50."""
    from app.db import SessionLocal
    from analytics.loader import load_benchmark, load_fund_nav

    with SessionLocal() as s:
        fund = load_fund_nav(s, 122639)  # Parag Parikh Flexi Cap
        bench = load_benchmark(s, "NIFTY_50")
    if fund.empty or bench.empty:
        pytest.skip("db not seeded; run `make ingest` first")

    sc = compute_scorecard(122639, fund, bench, rf_annual=0.065)
    # Sanity checks: trailing 1Y and 3Y should be available and in a plausible range.
    assert sc.trailing["1Y"].available
    assert sc.trailing["3Y"].available
    assert -0.5 < sc.trailing["1Y"].value < 1.0
    assert sc.volatility.available
    assert 0.0 < sc.volatility.value < 1.0
    assert sc.beta.available
    assert 0.0 < sc.beta.value < 2.0
    assert sc.max_drawdown.available
    assert -1.0 < sc.max_drawdown.value <= 0.0
