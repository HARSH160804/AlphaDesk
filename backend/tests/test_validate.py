"""Validation unit tests."""
from __future__ import annotations

from datetime import date

from ingestion.validate import validate_series


def test_drops_duplicates():
    pairs = [
        (date(2024, 1, 1), 100.0),
        (date(2024, 1, 1), 101.0),
        (date(2024, 1, 2), 102.0),
    ]
    cleaned, report = validate_series(pairs)
    assert len(cleaned) == 2
    assert report.duplicates == 1


def test_drops_non_positive():
    pairs = [
        (date(2024, 1, 1), 0.0),
        (date(2024, 1, 2), -1.0),
        (date(2024, 1, 3), 10.0),
    ]
    cleaned, report = validate_series(pairs)
    assert cleaned == [(date(2024, 1, 3), 10.0)]
    assert report.non_positive == 2


def test_flags_gaps_over_week():
    pairs = [
        (date(2024, 1, 1), 100.0),
        (date(2024, 1, 15), 101.0),  # 14-day gap
        (date(2024, 1, 16), 102.0),
    ]
    cleaned, report = validate_series(pairs)
    assert len(cleaned) == 3
    assert len(report.long_gaps) == 1
    start, end, gap = report.long_gaps[0]
    assert start == date(2024, 1, 1)
    assert end == date(2024, 1, 15)
    assert gap == 14


def test_sorts_output():
    pairs = [
        (date(2024, 1, 3), 103.0),
        (date(2024, 1, 1), 101.0),
        (date(2024, 1, 2), 102.0),
    ]
    cleaned, _ = validate_series(pairs)
    assert [p[0] for p in cleaned] == [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
    ]
