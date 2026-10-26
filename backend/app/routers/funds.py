"""`/api/funds` and `/api/funds/{code}` endpoints."""
from __future__ import annotations

import math
from typing import Literal, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from analytics.metrics import category_percentile_rank
from app.db import SessionLocal
from app.routers._builders import detail_from_bundle, summary_from_bundle
from app.schemas import Category, FundDetail, FundSummary
from app.services.scorecard import get_bundle, list_funds


router = APIRouter(prefix="/api/funds", tags=["funds"])

SortKey = Literal[
    "name",
    "category",
    "1Y", "3Y", "5Y",
    "vol", "sharpe", "sortino", "beta", "alpha", "max_dd",
]

_SORT_ACCESSOR = {
    "name": lambda s: s.name,
    "category": lambda s: s.category,
    "1Y":   lambda s: _vn(s.trailing.y1.value),
    "3Y":   lambda s: _vn(s.trailing.y3.value),
    "5Y":   lambda s: _vn(s.trailing.y5.value),
    "vol":  lambda s: _vn(s.volatility.value),
    "sharpe": lambda s: _vn(s.sharpe.value),
    "sortino": lambda s: _vn(s.sortino.value),
    "beta":  lambda s: _vn(s.beta.value),
    "alpha": lambda s: _vn(s.alpha.value),
    "max_dd": lambda s: _vn(s.max_drawdown.value),
}


def _vn(v: Optional[float]) -> float:
    """Normalise None / NaN so NaN sorts last in both directions."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return math.nan
    return v


@router.get(
    "",
    response_model=list[FundSummary],
    summary="List funds with optional filters, search and sort",
)
def list_funds_endpoint(
    category: Optional[Category] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Case-insensitive fund-name substring"),
    sort: SortKey = Query("3Y", description="Metric to sort by"),
    order: Literal["asc", "desc"] = Query("desc"),
    limit: int = Query(100, ge=1, le=500),
) -> list[FundSummary]:
    with SessionLocal() as session:
        funds = list_funds(session)
        bundles = [get_bundle(session, f.scheme_code) for f in funds]
        bundles = [b for b in bundles if b is not None]

        summaries = [summary_from_bundle(b) for b in bundles]

    # Attach category 3Y percentile rank so the dashboard can colour peer rows.
    frame = pd.DataFrame(
        [
            {
                "idx": i,
                "scheme_code": s.scheme_code,
                "category": s.category,
                "3Y": s.trailing.y3.value if s.trailing.y3.value is not None else float("nan"),
            }
            for i, s in enumerate(summaries)
        ]
    )
    if not frame.empty:
        frame["pct_rank"] = category_percentile_rank(
            frame, category_col="category", metric_col="3Y"
        )
        for _, row in frame.iterrows():
            val = row["pct_rank"]
            if not math.isnan(val):
                summaries[int(row["idx"])] = summaries[int(row["idx"])].model_copy(
                    update={"pct_rank_3y": float(val)}
                )

    # Filter
    if category:
        summaries = [s for s in summaries if s.category == category]
    if search:
        needle = search.lower().strip()
        summaries = [s for s in summaries if needle in s.name.lower()]

    # Sort — NaN always last, regardless of direction
    accessor = _SORT_ACCESSOR[sort]
    reverse = order == "desc"

    def _is_nan(v) -> bool:
        return isinstance(v, float) and math.isnan(v)

    def _key(s: FundSummary):
        v = accessor(s)
        if isinstance(v, (int, float)):
            return v
        return str(v).lower()

    finite = [s for s in summaries if not _is_nan(accessor(s))]
    nans = [s for s in summaries if _is_nan(accessor(s))]
    finite.sort(key=_key, reverse=reverse)
    summaries = finite + nans
    return summaries[:limit]


@router.get(
    "/{scheme_code}",
    response_model=FundDetail,
    responses={404: {"description": "Fund not found"}},
    summary="Full detail for one fund: metrics + series",
)
def get_fund_detail(scheme_code: int) -> FundDetail:
    with SessionLocal() as session:
        bundle = get_bundle(session, scheme_code)
    if bundle is None:
        raise HTTPException(status_code=404, detail=f"fund {scheme_code} not found")
    return detail_from_bundle(bundle)
