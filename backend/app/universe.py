"""Load the fund universe from config/funds.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config import get_settings


@dataclass(frozen=True)
class BenchmarkSpec:
    id: str
    name: str
    yf_ticker: str | None


@dataclass(frozen=True)
class FundSpec:
    scheme_code: int
    category: str
    benchmark_id: str


@dataclass(frozen=True)
class Universe:
    benchmarks: list[BenchmarkSpec]
    funds: list[FundSpec]

    def benchmark_by_id(self, bid: str) -> BenchmarkSpec | None:
        return next((b for b in self.benchmarks if b.id == bid), None)


def load_universe(path: Path | None = None) -> Universe:
    p = path or get_settings().funds_config_path
    with open(p, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    benchmarks = [
        BenchmarkSpec(id=b["id"], name=b["name"], yf_ticker=b.get("yf_ticker"))
        for b in raw.get("benchmarks", [])
    ]
    funds = [
        FundSpec(
            scheme_code=int(f["scheme_code"]),
            category=f["category"],
            benchmark_id=f["benchmark_id"],
        )
        for f in raw.get("funds", [])
    ]
    return Universe(benchmarks=benchmarks, funds=funds)
