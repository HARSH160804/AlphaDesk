"""Validation helpers for ingested NAV / benchmark series."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable


@dataclass
class ValidationReport:
    duplicates: int = 0
    non_positive: int = 0
    long_gaps: list[tuple[date, date, int]] = None  # (gap_start, gap_end, days)

    def __post_init__(self) -> None:
        if self.long_gaps is None:
            self.long_gaps = []

    @property
    def has_issues(self) -> bool:
        return bool(self.duplicates or self.non_positive or self.long_gaps)

    def summary(self) -> str:
        parts = []
        if self.duplicates:
            parts.append(f"{self.duplicates} duplicate rows dropped")
        if self.non_positive:
            parts.append(f"{self.non_positive} non-positive values dropped")
        if self.long_gaps:
            parts.append(f"{len(self.long_gaps)} gaps > 7 days")
        return "; ".join(parts) or "clean"


def validate_series(
    pairs: Iterable[tuple[date, float]],
    *,
    gap_threshold_days: int = 7,
) -> tuple[list[tuple[date, float]], ValidationReport]:
    """Deduplicate, drop invalid rows, flag gaps > threshold.

    `pairs` is iterable of (date, value). Returns the cleaned, sorted list
    and a report. The function never silently drops data: every removal is
    reflected in the report counts, and gaps longer than threshold calendar
    days are listed with their endpoints.
    """
    report = ValidationReport()
    seen: dict[date, float] = {}
    for d, v in pairs:
        if v is None or v <= 0 or v != v:  # NaN
            report.non_positive += 1
            continue
        if d in seen:
            report.duplicates += 1
            continue
        seen[d] = float(v)

    cleaned = sorted(seen.items(), key=lambda kv: kv[0])

    if len(cleaned) >= 2:
        for (d_prev, _), (d_cur, _) in zip(cleaned[:-1], cleaned[1:], strict=False):
            gap = (d_cur - d_prev).days
            if gap > gap_threshold_days:
                report.long_gaps.append((d_prev, d_cur, gap))

    return cleaned, report


def latest_date(pairs: Iterable[tuple[date, float]]) -> date | None:
    latest: date | None = None
    for d, _ in pairs:
        if latest is None or d > latest:
            latest = d
    return latest


def is_recent_enough(
    latest: date | None, *, max_staleness_days: int = 10, today: date | None = None
) -> bool:
    if latest is None:
        return False
    ref = today or date.today()
    return (ref - latest) <= timedelta(days=max_staleness_days)
