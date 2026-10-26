"""`/api/compare` — align N funds on common trading dates, rebase to 100."""
from __future__ import annotations

import math

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.db import SessionLocal
from app.routers._builders import summary_from_bundle
from app.schemas import CompareResponse, CompareSeriesPoint
from app.services.scorecard import get_bundle


router = APIRouter(prefix="/api/compare", tags=["funds"])


@router.get(
    "",
    response_model=CompareResponse,
    summary="Rebase N funds to 100 on their common start date",
)
def compare(
    codes: str = Query(
        ...,
        description="Comma-separated scheme codes (2 to 6). Example: `122639,118955,120716`.",
        pattern=r"^[0-9]+(,[0-9]+)*$",
    ),
) -> CompareResponse:
    try:
        parsed = [int(c) for c in codes.split(",") if c]
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(400, f"invalid codes: {exc}") from exc
    if not 2 <= len(parsed) <= 6:
        raise HTTPException(400, "codes must contain 2 to 6 scheme codes")
    if len(set(parsed)) != len(parsed):
        raise HTTPException(400, "duplicate scheme codes")

    with SessionLocal() as session:
        bundles = []
        missing: list[int] = []
        for code in parsed:
            b = get_bundle(session, code)
            if b is None or b.nav.empty:
                missing.append(code)
            else:
                bundles.append(b)
    if missing:
        raise HTTPException(404, f"unknown or empty funds: {missing}")

    # Align on inner intersection of trading dates
    series_map = {str(b.fund.scheme_code): b.nav for b in bundles}
    aligned = pd.concat(series_map, axis=1, join="inner")
    if aligned.empty or len(aligned) < 2:
        raise HTTPException(422, "no overlapping NAV dates across the selected funds")

    rebased = aligned.div(aligned.iloc[0]).mul(100.0)
    labels = list(rebased.columns)

    points: list[CompareSeriesPoint] = []
    for idx, row in rebased.iterrows():
        vals = {label: float(row[label]) for label in labels if not math.isnan(float(row[label]))}
        points.append(CompareSeriesPoint(date=idx.date(), values=vals))

    metrics = [summary_from_bundle(b) for b in bundles]

    return CompareResponse(
        labels=labels,
        aligned_start=aligned.index[0].date(),
        aligned_end=aligned.index[-1].date(),
        rebased=points,
        metrics=metrics,
    )
