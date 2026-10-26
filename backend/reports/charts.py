"""Matplotlib chart generators styled to the AlphaDesk palette.

Returns bytes buffers that both the PPTX and DOCX builders embed. One
place that controls chart appearance — never style per-slide.
"""
from __future__ import annotations

import io
from typing import Optional

import matplotlib
matplotlib.use("Agg")                                               # noqa: E402
import matplotlib.pyplot as plt                                     # noqa: E402
import matplotlib.ticker as mticker                                 # noqa: E402
import pandas as pd                                                 # noqa: E402

from reports.tokens import (
    ACCENT,
    HEX,
    NEUTRAL_100,
    NEUTRAL_200,
    NEUTRAL_400,
    NEUTRAL_600,
    NEUTRAL_900,
    NEG,
)


def _apply_base_style(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(HEX(NEUTRAL_200))
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=HEX(NEUTRAL_600), labelsize=9, length=0)
    ax.grid(True, which="major", axis="y", color=HEX(NEUTRAL_200), linewidth=0.8)
    ax.set_axisbelow(True)


def _finalise(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def rebased_chart(
    fund: pd.Series,
    bench: Optional[pd.Series],
    *,
    fund_label: str,
    bench_label: str,
    width_in: float = 10.0,
    height_in: float = 4.0,
) -> bytes:
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    _apply_base_style(ax)

    f = fund.copy()
    f = (f / f.iloc[0]) * 100.0
    ax.plot(f.index, f.values, color=HEX(ACCENT), linewidth=1.6, label=fund_label)

    if bench is not None and not bench.empty:
        b = bench.dropna()
        b = (b / b.iloc[0]) * 100.0
        ax.plot(
            b.index, b.values,
            color=HEX(NEUTRAL_600), linewidth=1.3,
            linestyle=(0, (4, 3)), label=bench_label,
        )

    ax.set_ylabel("Index (start = 100)", fontsize=10, color=HEX(NEUTRAL_600))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    _legend(ax)
    return _finalise(fig)


def drawdown_chart(
    dd_series: pd.Series,
    *,
    width_in: float = 10.0,
    height_in: float = 3.0,
) -> bytes:
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    _apply_base_style(ax)
    values = dd_series.values * 100.0
    ax.fill_between(dd_series.index, values, 0, color=HEX(NEG), alpha=0.10, linewidth=0)
    ax.plot(dd_series.index, values, color=HEX(NEG), linewidth=1.2)
    ax.axhline(0, color=HEX(NEUTRAL_200), linewidth=0.8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.set_ylabel("Drawdown", fontsize=10, color=HEX(NEUTRAL_600))
    return _finalise(fig)


def rolling_chart(
    df: pd.DataFrame,
    *,
    fund_label: str,
    bench_label: str,
    width_in: float = 10.0,
    height_in: float = 3.5,
) -> bytes:
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    _apply_base_style(ax)
    if "fund" in df.columns:
        ax.plot(df.index, df["fund"].values * 100.0,
                color=HEX(ACCENT), linewidth=1.5, label=fund_label)
    if "bench" in df.columns and df["bench"].notna().any():
        ax.plot(df.index, df["bench"].values * 100.0,
                color=HEX(NEUTRAL_600), linewidth=1.2,
                linestyle=(0, (4, 3)), label=bench_label)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylabel("Return", fontsize=10, color=HEX(NEUTRAL_600))
    _legend(ax)
    return _finalise(fig)


def calendar_year_bars(
    years: list[tuple[int, float, float | None]],
    *,
    width_in: float = 10.0,
    height_in: float = 3.5,
) -> bytes:
    """Grouped bars: fund vs benchmark per calendar year."""
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    _apply_base_style(ax)
    labels = [str(y) for y, _, _ in years]
    import numpy as np
    x = np.arange(len(labels))
    width = 0.38

    fund_vals = [f * 100 for _, f, _ in years]
    bench_vals = [(b * 100 if b is not None else 0.0) for _, _, b in years]
    has_bench = any(b is not None for _, _, b in years)

    ax.bar(
        x - (width / 2 if has_bench else 0),
        fund_vals,
        width if has_bench else width * 1.5,
        color=HEX(ACCENT),
        label="Fund",
    )
    if has_bench:
        ax.bar(
            x + width / 2,
            bench_vals,
            width,
            color=HEX(NEUTRAL_400),
            label="Benchmark",
        )

    ax.axhline(0, color=HEX(NEUTRAL_200), linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylabel("Calendar-year return", fontsize=10, color=HEX(NEUTRAL_600))
    if has_bench:
        _legend(ax)
    return _finalise(fig)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _legend(ax: plt.Axes) -> None:
    leg = ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=10,
        labelcolor=HEX(NEUTRAL_900),
        handlelength=1.5,
    )
    if leg:
        leg.set_bbox_to_anchor((0.0, 1.08))


_ = NEUTRAL_100  # kept intentionally for future surface use
