"""Universe loader tests."""
from __future__ import annotations

from app.universe import load_universe


def test_load_universe_shape():
    uni = load_universe()
    # 29 funds confirmed against mfapi, plus 4 benchmarks.
    assert len(uni.benchmarks) == 4
    assert len(uni.funds) == 29

    categories = {f.category for f in uni.funds}
    assert categories == {
        "large_cap",
        "mid_cap",
        "small_cap",
        "flexi_cap",
        "index",
        "short_debt",
    }

    # every fund points at a benchmark that exists
    bids = {b.id for b in uni.benchmarks}
    assert all(f.benchmark_id in bids for f in uni.funds)
