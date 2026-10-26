"""Pydantic response models for the public API.

The guiding principle: every numeric metric is wrapped in `MetricPayload`
so NaN carries a reason. Series payloads (NAV, drawdown, rolling) use
ISO date strings so the JSON stays plain.
"""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["large_cap", "mid_cap", "small_cap", "flexi_cap", "index", "short_debt"]
ReportFormat = Literal["pptx", "docx"]
Period = Literal["1Y", "3Y", "5Y", "SI"]


class MetricPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Optional[float] = Field(
        default=None, description="Metric value, or null when unavailable."
    )
    reason: Optional[str] = Field(
        default=None, description="Human-readable reason when value is null."
    )

    @classmethod
    def from_metric(cls, mv) -> "MetricPayload":
        """Build from analytics.metrics.MetricValue (or NaN float)."""
        if mv is None:
            return cls(value=None, reason="not computed")
        if hasattr(mv, "value"):
            v = mv.value
            reason = mv.reason
        else:
            v = float(mv)
            reason = None
        if isinstance(v, float) and math.isnan(v):
            return cls(value=None, reason=reason or "not available")
        return cls(value=float(v), reason=None)


class TrailingReturns(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    m1: MetricPayload = Field(alias="1M")
    m3: MetricPayload = Field(alias="3M")
    m6: MetricPayload = Field(alias="6M")
    y1: MetricPayload = Field(alias="1Y")
    y3: MetricPayload = Field(alias="3Y")
    y5: MetricPayload = Field(alias="5Y")


class FundRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scheme_code: int
    name: str
    category: Category
    amc: Optional[str] = None
    benchmark_id: Optional[str] = None


class FundSummary(FundRef):
    """Row shape for `GET /api/funds`."""
    as_of: Optional[date] = None
    trailing: TrailingReturns
    volatility: MetricPayload
    max_drawdown: MetricPayload
    sharpe: MetricPayload
    sortino: MetricPayload
    beta: MetricPayload
    alpha: MetricPayload
    pct_rank_3y: Optional[float] = Field(
        default=None, description="Category percentile rank by 3Y CAGR (0-100)."
    )


class NavPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    nav: float


class DrawdownPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    drawdown: float  # nonpositive


class RollingPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    fund: float
    bench: Optional[float] = None


class DrawdownEpisode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    peak_date: date
    trough_date: date
    recovery_date: Optional[date] = None
    max_drawdown: float


class FundDetail(FundSummary):
    """Full payload for `GET /api/funds/{code}`."""
    tracking_error: MetricPayload
    information_ratio: MetricPayload
    up_capture: MetricPayload
    down_capture: MetricPayload
    nav_series: list[NavPoint]
    bench_series: list[NavPoint] = Field(default_factory=list)
    drawdown_series: list[DrawdownPoint]
    worst_drawdown: Optional[DrawdownEpisode] = None
    rolling_1y: list[RollingPoint]
    rolling_3y: list[RollingPoint]


class CompareSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    values: dict[str, float]  # label -> rebased price


class CompareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    labels: list[str]  # fund code or benchmark id, as string
    aligned_start: date
    aligned_end: date
    rebased: list[CompareSeriesPoint]
    metrics: list[FundSummary]


class CategoryBest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scheme_code: int
    name: str
    value: float


class CategorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    fund_count: int
    avg_1y: Optional[float] = None
    avg_3y: Optional[float] = None
    avg_5y: Optional[float] = None
    avg_vol: Optional[float] = None
    avg_max_drawdown: Optional[float] = None
    best_3y: Optional[CategoryBest] = None
    worst_3y: Optional[CategoryBest] = None


class IngestionStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    funds_processed: int
    benchmarks_processed: int
    rows_inserted: int
    errors: Optional[list[str]] = None
    warnings: Optional[list[str]] = None


class IngestionTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accepted: bool
    message: str
    run_id: Optional[int] = None


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codes: list[int] = Field(..., min_length=1, max_length=10)
    format: ReportFormat
    period: Period = "3Y"


class ApiError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: str
