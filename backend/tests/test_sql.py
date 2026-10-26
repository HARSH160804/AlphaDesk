"""Smoke tests for the /api/sql endpoint: every whitelisted query runs and
returns a plausibly shaped result set against the live DB.

If the DB isn't seeded (fresh checkout, no `make ingest`), tests skip gracefully.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sql_endpoint import QUERIES


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _skip_if_empty(client: TestClient) -> None:
    stats = client.get("/api/stats").json()
    if stats.get("funds", 0) == 0 or stats.get("nav_rows", 0) == 0:
        pytest.skip("database not seeded; run `make ingest` first")


def test_list_queries(client: TestClient) -> None:
    r = client.get("/api/sql")
    assert r.status_code == 200
    assert set(r.json()["queries"]) == set(QUERIES.keys())


@pytest.mark.parametrize("name", list(QUERIES.keys()))
def test_each_query_runs(client: TestClient, name: str) -> None:
    _skip_if_empty(client)
    r = client.get(f"/api/sql/{name}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["query"] == name
    assert body["row_count"] >= 1
    assert isinstance(body["rows"], list)
    assert isinstance(body["rows"][0], dict)


def test_unknown_query_404(client: TestClient) -> None:
    r = client.get("/api/sql/not_a_real_query")
    assert r.status_code == 404


def test_category_leaderboard_has_rank_column(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/sql/category_leaderboard_3y")
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert any("category_rank" in row for row in rows)
    # Each category should have at least one rank == 1
    by_cat_top = {row["category"] for row in rows if row["category_rank"] == 1}
    assert len(by_cat_top) >= 4  # we have 6 categories; some may miss 3Y history


def test_worst_month_is_2020_03_for_equities(client: TestClient) -> None:
    _skip_if_empty(client)
    r = client.get("/api/sql/worst_drawdown_month_by_cat")
    assert r.status_code == 200
    by_cat = {row["category"]: row for row in r.json()["rows"]}
    # Covid crash should dominate for every equity category.
    for cat in ("large_cap", "mid_cap", "small_cap", "flexi_cap", "index"):
        assert by_cat[cat]["year_month"] == "2020-03"
        assert by_cat[cat]["cat_avg_return"] < -0.15
