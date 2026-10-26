"""Endpoint tests for the Phase 4 API.

These run against the live SQLite DB populated in Phase 1. Tests skip gracefully
when the DB hasn't been seeded.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _skip_if_empty(client: TestClient) -> None:
    stats = client.get("/api/stats").json()
    if stats.get("funds", 0) == 0 or stats.get("nav_rows", 0) == 0:
        pytest.skip("database not seeded; run `make ingest` first")


# ---------- /api/funds ----------


def test_list_funds_default(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 20  # we have 29 funds in the universe
    row = body[0]
    for key in ("scheme_code", "name", "category", "trailing", "volatility",
                "max_drawdown", "sharpe", "beta"):
        assert key in row
    # Trailing table uses the alias keys ("1M", "1Y", ...)
    assert set(row["trailing"].keys()) == {"1M", "3M", "6M", "1Y", "3Y", "5Y"}


def test_list_funds_category_filter(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds?category=small_cap")
    body = r.json()
    assert all(row["category"] == "small_cap" for row in body)
    assert len(body) == 5


def test_list_funds_search(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds?search=parag")
    body = r.json()
    assert len(body) == 1
    assert "Parag Parikh" in body[0]["name"]


def test_list_funds_sort_by_3y_desc(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds?sort=3Y&order=desc")
    body = r.json()
    values = [row["trailing"]["3Y"]["value"] for row in body]
    finite = [v for v in values if v is not None]
    assert finite == sorted(finite, reverse=True)
    # NaN values must come last
    for v in values[len(finite):]:
        assert v is None


def test_list_funds_sort_by_max_dd_asc(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds?sort=max_dd&order=asc")
    body = r.json()
    vals = [row["max_drawdown"]["value"] for row in body if row["max_drawdown"]["value"] is not None]
    assert vals == sorted(vals)


def test_list_funds_limit(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds?limit=5")
    assert len(r.json()) == 5


def test_list_funds_pct_rank_filled(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds")
    body = r.json()
    # Every category must have at least one 100-percentile row.
    by_cat_top = {row["category"] for row in body if row.get("pct_rank_3y") == 100.0}
    assert "mid_cap" in by_cat_top
    assert "small_cap" in by_cat_top


# ---------- /api/funds/{code} ----------


def test_fund_detail_shape(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/funds/122639")  # Parag Parikh Flexi Cap
    assert r.status_code == 200
    body = r.json()
    assert body["scheme_code"] == 122639
    assert "Parag Parikh" in body["name"]
    assert len(body["nav_series"]) > 1000
    assert len(body["drawdown_series"]) == len(body["nav_series"])
    assert len(body["rolling_1y"]) > 0
    assert len(body["rolling_3y"]) > 0
    assert body["worst_drawdown"] is not None
    assert body["worst_drawdown"]["max_drawdown"] < 0


def test_fund_detail_covid_drawdown(client: TestClient) -> None:
    """Parag Parikh's historical trough is in March 2020."""
    _skip_if_empty(client)
    body = client.get("/api/funds/122639").json()
    assert body["worst_drawdown"]["trough_date"].startswith("2020-03")


def test_fund_detail_not_found(client: TestClient) -> None:
    r = client.get("/api/funds/9999999")
    assert r.status_code == 404


# ---------- /api/compare ----------


def test_compare_basic(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/compare?codes=122639,118955,120716")
    assert r.status_code == 200
    body = r.json()
    assert body["labels"] == ["122639", "118955", "120716"]
    # First rebased point is 100 for every label
    first = body["rebased"][0]["values"]
    for label in body["labels"]:
        assert first[label] == pytest.approx(100.0)
    # Series sorted ascending
    dates = [p["date"] for p in body["rebased"]]
    assert dates == sorted(dates)
    assert len(body["metrics"]) == 3


def test_compare_rejects_single_code(client: TestClient) -> None:
    r = client.get("/api/compare?codes=122639")
    assert r.status_code == 400


def test_compare_rejects_duplicates(client: TestClient) -> None:
    r = client.get("/api/compare?codes=122639,122639")
    assert r.status_code == 400


def test_compare_404_on_unknown_fund(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/compare?codes=122639,9999999")
    assert r.status_code == 404


# ---------- /api/categories/summary ----------


def test_categories_summary(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/categories/summary")
    assert r.status_code == 200
    body = r.json()
    cats = {row["category"]: row for row in body}
    expected = {"large_cap", "mid_cap", "small_cap", "flexi_cap", "index", "short_debt"}
    assert expected.issubset(cats.keys())
    for cat, row in cats.items():
        assert row["fund_count"] >= 1
        if cat != "short_debt":
            # Equity categories should always have an identifiable best / worst.
            assert row["best_3y"] is not None
            assert row["worst_3y"] is not None
            assert row["best_3y"]["value"] >= row["worst_3y"]["value"]


# ---------- /api/ingest ----------


def test_ingest_status(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/ingest/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"success", "failed", "running"}
    assert body["funds_processed"] >= 0


# ---------- /api/reports (stub) ----------


def test_reports_stub_returns_501(client: TestClient) -> None:
    r = client.post(
        "/api/reports",
        json={"codes": [122639], "format": "pptx", "period": "3Y"},
    )
    assert r.status_code == 501


def test_reports_body_validation(client: TestClient) -> None:
    # format must be in enum
    r = client.post(
        "/api/reports",
        json={"codes": [122639], "format": "xlsx", "period": "3Y"},
    )
    assert r.status_code == 422


# ---------- OpenAPI ----------


def test_openapi_has_all_tags(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    tags_in_paths = set()
    for ops in schema["paths"].values():
        for op in ops.values():
            if isinstance(op, dict) and "tags" in op:
                tags_in_paths.update(op["tags"])
    for required in ("funds", "categories", "sql", "ingestion", "reports", "meta"):
        assert required in tags_in_paths
