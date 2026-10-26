"""PPTX deck builder — 16:9, consistent typography, no default theme.

Layout primitives (slide title bar, body text box, table) stay in this file so
appearance stays coherent; the per-slide functions below describe only what
goes on the slide. The output is written to a BytesIO.
"""
from __future__ import annotations

import io
from datetime import date
from typing import Iterable, Sequence

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

from reports import charts
from reports.context import ReportContext
from reports.tokens import (
    ACCENT, FONT_SANS, FONT_SANS_FALLBACK,
    FS_BODY, FS_H1, FS_H2, FS_HERO, FS_LABEL, FS_SMALL,
    NEG, NEUTRAL_200, NEUTRAL_400, NEUTRAL_600, NEUTRAL_900, POS,
    WHITE,
    pptx_rgb,
)


SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN  = Inches(0.6)
GUTTER  = Inches(0.3)


def build_pptx(ctx: ReportContext) -> bytes:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _title_slide(prs, ctx)
    _summary_slide(prs, ctx)
    _performance_slide(prs, ctx)
    _trailing_returns_slide(prs, ctx)
    _calendar_year_slide(prs, ctx)
    _risk_slide(prs, ctx)
    _drawdown_slide(prs, ctx)
    _rolling_slide(prs, ctx)
    _peer_slide(prs, ctx)
    _methodology_slide(prs, ctx)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Primitives — the only place we style
# ---------------------------------------------------------------------------


def _add_blank_slide(prs: Presentation):
    layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(layout)
    # Fill the whole slide white so the viewer theme doesn't leak through.
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.line.fill.background()
    bg.fill.solid()
    bg.fill.fore_color.rgb = pptx_rgb(WHITE)
    bg.shadow.inherit = False
    return slide


def _add_title_bar(slide, title: str, eyebrow: str | None = None) -> Inches:
    """Returns the Y position where the body content should start."""
    y = MARGIN
    if eyebrow:
        _add_text(
            slide, MARGIN, y, SLIDE_W - 2 * MARGIN, Inches(0.3),
            eyebrow.upper(), size=FS_LABEL, color=NEUTRAL_400,
            bold=False, letter_spacing=120,
        )
        y += Inches(0.3)
    _add_text(
        slide, MARGIN, y, SLIDE_W - 2 * MARGIN, Inches(0.55),
        title, size=FS_H1, color=NEUTRAL_900, bold=True,
    )
    y += Inches(0.55)
    # 1pt accent underline
    rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, MARGIN, y + Emu(5000), Inches(0.6), Emu(14000)
    )
    rule.line.fill.background()
    rule.fill.solid()
    rule.fill.fore_color.rgb = pptx_rgb(ACCENT)
    rule.shadow.inherit = False
    return y + Inches(0.25)


def _add_footer(slide, ctx: ReportContext, slide_no: int, total: int) -> None:
    y = SLIDE_H - Inches(0.4)
    width = (SLIDE_W - 2 * MARGIN) / 2
    _add_text(
        slide, MARGIN, y, width, Inches(0.25),
        f"AlphaDesk · {ctx.display_name}", size=FS_LABEL, color=NEUTRAL_400,
    )
    _add_text(
        slide, MARGIN + width, y, width, Inches(0.25),
        f"As of {ctx.as_of:%d %b %Y}   ·   {slide_no} / {total}",
        size=FS_LABEL, color=NEUTRAL_400, align=PP_ALIGN.RIGHT,
    )


def _add_text(
    slide, x, y, w, h,
    text: str,
    *,
    size: int = FS_BODY,
    color: tuple[int, int, int] = NEUTRAL_900,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    letter_spacing: int = 0,
    anchor=MSO_ANCHOR.TOP,
):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT_SANS
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = pptx_rgb(color)
    if letter_spacing:
        # python-pptx doesn't expose letter-spacing directly; we rely on uppercase + weight.
        pass
    _ = FONT_SANS_FALLBACK
    return box


def _add_table(
    slide, x, y, w, h,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    numeric_cols: Iterable[int] = (),
    tone_cols: dict[int, Iterable[float | None]] = None,
):
    """Table with hairline borders, right-aligned numeric columns."""
    table_shape = slide.shapes.add_table(
        rows=len(rows) + 1, cols=len(headers), left=x, top=y, width=w, height=h
    )
    table = table_shape.table
    numeric_set = set(numeric_cols)

    for ci, header in enumerate(headers):
        cell = table.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = pptx_rgb((248, 250, 252))
        tf = cell.text_frame
        tf.margin_left = tf.margin_right = Emu(50000)
        tf.margin_top = tf.margin_bottom = Emu(30000)
        tf.text = ""
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT if ci in numeric_set else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = header
        r.font.name = FONT_SANS
        r.font.size = Pt(FS_LABEL)
        r.font.bold = True
        r.font.color.rgb = pptx_rgb(NEUTRAL_600)

    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            cell = table.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = pptx_rgb(WHITE)
            tf = cell.text_frame
            tf.margin_left = tf.margin_right = Emu(50000)
            tf.margin_top = tf.margin_bottom = Emu(30000)
            tf.text = ""
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT if ci in numeric_set else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = val
            r.font.name = FONT_SANS
            r.font.size = Pt(FS_SMALL)
            colour = NEUTRAL_900
            if tone_cols and ci in tone_cols:
                tones = list(tone_cols[ci])
                if ri - 1 < len(tones) and tones[ri - 1] is not None:
                    t = tones[ri - 1]
                    if t > 0:
                        colour = POS
                    elif t < 0:
                        colour = NEG
            r.font.color.rgb = pptx_rgb(colour)

    return table


def _add_chart(slide, x, y, w, h, png_bytes: bytes) -> None:
    slide.shapes.add_picture(io.BytesIO(png_bytes), x, y, width=w, height=h)


def _add_stat_card(slide, x, y, w, h, label: str, value: str, secondary: str | None = None,
                   value_color: tuple[int, int, int] = NEUTRAL_900) -> None:
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    card.fill.solid()
    card.fill.fore_color.rgb = pptx_rgb((248, 250, 252))
    card.line.color.rgb = pptx_rgb(NEUTRAL_200)
    card.line.width = Emu(6350)
    card.shadow.inherit = False

    pad = Inches(0.15)
    _add_text(slide, x + pad, y + pad, w - 2 * pad, Inches(0.3),
              label.upper(), size=FS_LABEL, color=NEUTRAL_400, bold=False)
    _add_text(slide, x + pad, y + pad + Inches(0.3), w - 2 * pad, Inches(0.5),
              value, size=FS_H2, color=value_color, bold=True)
    if secondary:
        _add_text(slide, x + pad, y + h - Inches(0.4), w - 2 * pad, Inches(0.3),
                  secondary, size=FS_SMALL, color=NEUTRAL_600)


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

TOTAL_SLIDES = 10


def _title_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)

    _add_text(
        slide, MARGIN, Inches(1.6), SLIDE_W - 2 * MARGIN, Inches(0.4),
        "FUND SCORECARD", size=FS_LABEL, color=NEUTRAL_400,
    )
    _add_text(
        slide, MARGIN, Inches(2.0), SLIDE_W - 2 * MARGIN, Inches(1.6),
        ctx.display_name, size=FS_HERO, color=NEUTRAL_900, bold=True,
    )
    _add_text(
        slide, MARGIN, Inches(3.6), SLIDE_W - 2 * MARGIN, Inches(0.5),
        f"{(ctx.fund.amc or '—')} · benchmarked against {ctx.fund.benchmark_id or 'none'} · {ctx.period} window",
        size=FS_BODY, color=NEUTRAL_600,
    )

    rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, MARGIN, Inches(4.4), Inches(1.0), Emu(25000)
    )
    rule.line.fill.background()
    rule.fill.solid()
    rule.fill.fore_color.rgb = pptx_rgb(ACCENT)
    rule.shadow.inherit = False

    _add_text(
        slide, MARGIN, SLIDE_H - Inches(0.8), SLIDE_W - 2 * MARGIN, Inches(0.3),
        f"Prepared {date.today():%d %b %Y}  ·  AlphaDesk",
        size=FS_SMALL, color=NEUTRAL_400,
    )


def _summary_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Executive summary", "Three takeaways")

    content_h = Inches(5.0)
    card_w = (SLIDE_W - 2 * MARGIN - 2 * GUTTER) / 3
    for i, text in enumerate(ctx.takeaways):
        x = MARGIN + i * (card_w + GUTTER)
        _add_stat_card(slide, x, y, card_w, Inches(2.2),
                       f"Takeaway {i + 1}", "", secondary=None)
        _add_text(
            slide, x + Inches(0.15), y + Inches(0.5), card_w - Inches(0.3), Inches(1.6),
            text, size=FS_BODY, color=NEUTRAL_900,
        )
    _ = content_h
    _add_footer(slide, ctx, 2, TOTAL_SLIDES)


def _performance_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(
        slide, f"Performance vs {ctx.fund.benchmark_id or 'benchmark'}",
        f"{ctx.period} window — rebased to 100",
    )
    png = charts.rebased_chart(
        ctx.nav_series,
        ctx.bench_series,
        fund_label=ctx.fund.name.split(" - ")[0],
        bench_label=ctx.fund.benchmark_id or "Benchmark",
        width_in=11.5,
        height_in=4.8,
    )
    _add_chart(slide, MARGIN, y + Inches(0.1), Inches(12.1), Inches(5.0), png)
    _add_footer(slide, ctx, 3, TOTAL_SLIDES)


def _trailing_returns_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Trailing returns", "Absolute for < 1Y; CAGR for ≥ 1Y")

    headers = ["Metric", "1M", "3M", "6M", "1Y", "3Y", "5Y"]
    keys = ["1M", "3M", "6M", "1Y", "3Y", "5Y"]
    tr = ctx.scorecard.trailing

    def _fmt(k: str) -> str:
        m = tr.get(k)
        if m is None or not m.available:
            return "—"
        return f"{m.value * 100:+.2f}%"

    tones = [tr[k].value if tr.get(k) and tr[k].available else None for k in keys]

    rows = [[ctx.display_name.split(" - ")[0]] + [_fmt(k) for k in keys]]
    _add_table(
        slide, MARGIN, y + Inches(0.2),
        SLIDE_W - 2 * MARGIN, Inches(1.0),
        headers, rows,
        numeric_cols=range(1, len(headers)),
        tone_cols={i + 1: [tones[i]] for i in range(len(keys))},
    )

    # Risk sub-table underneath
    risk_headers = ["Volatility (ann.)", "Max drawdown", "Sharpe", "Sortino"]
    risk_rows = [[
        f"{ctx.scorecard.volatility.value * 100:.2f}%" if ctx.scorecard.volatility.available else "—",
        f"{ctx.scorecard.max_drawdown.value * 100:+.2f}%" if ctx.scorecard.max_drawdown.available else "—",
        f"{ctx.scorecard.sharpe.value:.2f}" if ctx.scorecard.sharpe.available else "—",
        f"{ctx.scorecard.sortino.value:.2f}" if ctx.scorecard.sortino.available else "—",
    ]]
    _add_table(
        slide, MARGIN, y + Inches(1.9),
        SLIDE_W - 2 * MARGIN, Inches(1.0),
        risk_headers, risk_rows,
        numeric_cols=range(len(risk_headers)),
        tone_cols={1: [ctx.scorecard.max_drawdown.value if ctx.scorecard.max_drawdown.available else None]},
    )

    _add_footer(slide, ctx, 4, TOTAL_SLIDES)


def _calendar_year_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Calendar-year returns", "Fund vs benchmark")
    years = [(c.year, c.fund_return, c.bench_return) for c in ctx.calendar_years]
    if years:
        png = charts.calendar_year_bars(years, width_in=11.5, height_in=4.2)
        _add_chart(slide, MARGIN, y + Inches(0.2), Inches(12.1), Inches(4.4), png)
    _add_footer(slide, ctx, 5, TOTAL_SLIDES)


def _risk_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Risk metrics", f"vs {ctx.fund.benchmark_id or '—'}")

    sc = ctx.scorecard
    cards = [
        ("Volatility (ann.)", _pct(sc.volatility), None),
        ("Max drawdown", _pct(sc.max_drawdown, signed=True), NEG if sc.max_drawdown.available and sc.max_drawdown.value < 0 else NEUTRAL_900),
        ("Sharpe", _num(sc.sharpe), None),
        ("Sortino", _num(sc.sortino), None),
        ("Beta", _num(sc.beta), None),
        ("Jensen's α (ann.)", _pct(sc.alpha, signed=True),
         POS if sc.alpha.available and sc.alpha.value > 0 else (NEG if sc.alpha.available and sc.alpha.value < 0 else NEUTRAL_900)),
        ("Tracking error", _pct(sc.tracking_error), None),
        ("Information ratio", _num(sc.information_ratio), None),
    ]
    cols = 4
    rows = (len(cards) + cols - 1) // cols
    card_w = (SLIDE_W - 2 * MARGIN - (cols - 1) * GUTTER) / cols
    card_h = Inches(1.4)
    for i, (label, value, colour) in enumerate(cards):
        r, c = divmod(i, cols)
        x = MARGIN + c * (card_w + GUTTER)
        yy = y + Inches(0.1) + r * (card_h + GUTTER)
        _add_stat_card(slide, x, yy, card_w, card_h, label, value,
                       value_color=colour or NEUTRAL_900)
    _ = rows
    _add_footer(slide, ctx, 6, TOTAL_SLIDES)


def _drawdown_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Drawdown over time", f"Within the {ctx.period} window")
    if not ctx.drawdown_series.empty:
        png = charts.drawdown_chart(ctx.drawdown_series, width_in=11.5, height_in=3.4)
        _add_chart(slide, MARGIN, y + Inches(0.2), Inches(12.1), Inches(3.6), png)
    if ctx.worst_drawdown is not None:
        wd = ctx.worst_drawdown
        info_y = y + Inches(4.3)
        rec = wd.recovery_date.strftime("%d %b %Y") if wd.recovery_date else "Not yet recovered"
        _add_text(
            slide, MARGIN, info_y, SLIDE_W - 2 * MARGIN, Inches(0.3),
            f"Worst drawdown: {wd.max_drawdown * 100:+.2f}%   ·   "
            f"Peak {wd.peak_date:%d %b %Y}   ·   Trough {wd.trough_date:%d %b %Y}   ·   Recovered {rec}",
            size=FS_BODY, color=NEUTRAL_600,
        )
    _add_footer(slide, ctx, 7, TOTAL_SLIDES)


def _rolling_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Rolling 3Y CAGR", "Consistency check across the window")
    if not ctx.rolling_3y.empty:
        png = charts.rolling_chart(
            ctx.rolling_3y,
            fund_label=ctx.fund.name.split(" - ")[0],
            bench_label=ctx.fund.benchmark_id or "Benchmark",
            width_in=11.5,
            height_in=4.4,
        )
        _add_chart(slide, MARGIN, y + Inches(0.1), Inches(12.1), Inches(4.6), png)
    _add_footer(slide, ctx, 8, TOTAL_SLIDES)


def _peer_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(
        slide, "Peer ranking",
        f"Within {ctx.fund.category.replace('_', ' ').title()} · 3Y CAGR",
    )

    rows = []
    tone = []
    for p in ctx.peer_leaderboard:
        rows.append([
            p.name.split(" - ")[0],
            f"#{p.scheme_code}",
            f"{p.return_3y * 100:.2f}%",
            "◆ this fund" if p.is_subject else "",
        ])
        tone.append(p.return_3y)
    _add_table(
        slide, MARGIN, y + Inches(0.2),
        SLIDE_W - 2 * MARGIN, Inches(0.4) + Inches(0.35) * len(rows),
        ["Fund", "Code", "3Y CAGR", ""], rows,
        numeric_cols=(1, 2),
        tone_cols={2: tone},
    )
    _add_footer(slide, ctx, 9, TOTAL_SLIDES)


def _methodology_slide(prs, ctx: ReportContext) -> None:
    slide = _add_blank_slide(prs)
    y = _add_title_bar(slide, "Methodology & disclaimer")

    bullets = [
        "Returns are computed from daily NAVs sourced from mfapi.in.",
        "Benchmark data: Nifty price indices via yfinance.",
        "Trailing returns < 1Y are absolute; ≥ 1Y are CAGR using calendar-day gaps.",
        "Risk statistics use sample standard deviation (ddof=1), 252 trading days per year.",
        f"Risk-free rate for Sharpe / Sortino: {ctx.scorecard.sharpe.reason or '6.50% p.a.'}",
        "Peer ranking recomputed every ingest against the fund's category peers.",
    ]
    body = "\n".join([f"•  {b}" for b in bullets])
    _add_text(
        slide, MARGIN, y + Inches(0.1), SLIDE_W - 2 * MARGIN, Inches(2.8),
        body, size=FS_BODY, color=NEUTRAL_900,
    )

    _add_text(
        slide, MARGIN, y + Inches(3.3), SLIDE_W - 2 * MARGIN, Inches(0.3),
        "DISCLAIMER", size=FS_LABEL, color=NEUTRAL_400,
    )
    disc = "\n".join([f"•  {d}" for d in ctx.disclaimers])
    _add_text(
        slide, MARGIN, y + Inches(3.6), SLIDE_W - 2 * MARGIN, Inches(2.4),
        disc, size=FS_SMALL, color=NEUTRAL_600,
    )
    _add_footer(slide, ctx, 10, TOTAL_SLIDES)


# ---------------------------------------------------------------------------
# small formatters
# ---------------------------------------------------------------------------


def _pct(m, signed: bool = False) -> str:
    if m is None or not m.available:
        return "—"
    return f"{m.value * 100:+.2f}%" if signed else f"{m.value * 100:.2f}%"


def _num(m) -> str:
    if m is None or not m.available:
        return "—"
    return f"{m.value:.2f}"
