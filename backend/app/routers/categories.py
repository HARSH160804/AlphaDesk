"""`/api/categories/summary` — one row per category with aggregates + best/worst."""
from __future__ import annotations

import math
from statistics import mean
from typing import Optional

from fastapi import APIRouter

from app.db import SessionLocal
from app.routers._builders import summary_from_bundle
from app.schemas import CategoryBest, CategorySummary
from app.services.scorecard import get_bundle, list_funds


router = APIRouter(prefix="/api/categories", tags=["categories"])


def _mean_or_none(values: list[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    return mean(clean) if clean else None


@router.get(
    "/summary",
    response_model=list[CategorySummary],
    summary="Per-category count, average metrics, best and worst by 3Y CAGR",
)
def categories_summary() -> list[CategorySummary]:
    with SessionLocal() as session:
        funds = list_funds(session)
        bundles = [get_bundle(session, f.scheme_code) for f in funds]
        summaries = [summary_from_bundle(b) for b in bundles if b is not None]

    by_cat: dict[str, list] = {}
    for s in summaries:
        by_cat.setdefault(s.category, []).append(s)

    out: list[CategorySummary] = []
    for category, rows in by_cat.items():
        y3_values = [r.trailing.y3.value for r in rows]
        best = None
        worst = None
        valid = [r for r in rows if r.trailing.y3.value is not None and not math.isnan(r.trailing.y3.value)]
        if valid:
            best_row = max(valid, key=lambda r: r.trailing.y3.value)
            worst_row = min(valid, key=lambda r: r.trailing.y3.value)
            best = CategoryBest(
                scheme_code=best_row.scheme_code,
                name=best_row.name,
                value=float(best_row.trailing.y3.value),
            )
            worst = CategoryBest(
                scheme_code=worst_row.scheme_code,
                name=worst_row.name,
                value=float(worst_row.trailing.y3.value),
            )

        out.append(
            CategorySummary(
                category=category,  # type: ignore[arg-type]
                fund_count=len(rows),
                avg_1y=_mean_or_none([r.trailing.y1.value for r in rows]),
                avg_3y=_mean_or_none(y3_values),
                avg_5y=_mean_or_none([r.trailing.y5.value for r in rows]),
                avg_vol=_mean_or_none([r.volatility.value for r in rows]),
                avg_max_drawdown=_mean_or_none([r.max_drawdown.value for r in rows]),
                best_3y=best,
                worst_3y=worst,
            )
        )

    out.sort(key=lambda c: c.category)
    return out
