"""Ingestion orchestration: resolve universe -> fetch -> validate -> upsert."""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import session_scope
from app.logging_setup import configure_logging
from app.models import Benchmark, BenchmarkHistory, Fund, IngestionRun, NavHistory
from app.universe import FundSpec, Universe, load_universe
from ingestion.benchmark_client import fetch_benchmark_history
from ingestion.mfapi_client import MfApiClient, MfApiError, SchemeData
from ingestion.validate import ValidationReport, validate_series

logger = logging.getLogger("ingestion")

# Map scheme_category strings from mfapi to our normalized AMC-free category.
_PLAN_SUFFIX = " - Direct Plan - Growth"


@dataclass
class RunResult:
    rows_inserted: int = 0
    funds_processed: int = 0
    benchmarks_processed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _is_sqlite(session: Session) -> bool:
    return session.get_bind().dialect.name == "sqlite"


def _upsert_rows(session: Session, table, rows: list[dict], index_cols: list[str]) -> int:
    """Idempotent upsert that returns a conservative inserted-row count.

    Postgres: ON CONFLICT DO UPDATE on the unique index.
    SQLite:   ON CONFLICT DO UPDATE on the unique index.
    """
    if not rows:
        return 0
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        stmt = pg_insert(table).values(rows)
        update_cols = {c.name: stmt.excluded[c.name] for c in table.c if c.name not in index_cols and c.name != "id"}
        stmt = stmt.on_conflict_do_update(index_elements=index_cols, set_=update_cols)
        session.execute(stmt)
    elif dialect == "sqlite":
        # SQLite's upsert matches on the unique constraint, not the column list directly.
        stmt = sqlite_insert(table).values(rows)
        update_cols = {c.name: stmt.excluded[c.name] for c in table.c if c.name not in index_cols and c.name != "id"}
        stmt = stmt.on_conflict_do_update(index_elements=index_cols, set_=update_cols)
        session.execute(stmt)
    else:
        raise RuntimeError(f"unsupported dialect for upsert: {dialect}")
    return len(rows)


def _canonical_fund_name(scheme_name: str) -> str:
    # Normalise minor cosmetic variations like " - Direct Plan - Growth Option" / "- GROWTH".
    name = scheme_name.strip()
    for suffix in (
        " - Direct Plan - Growth Option",
        " - Direct Plan - GROWTH",
        " - Direct Plan - Growth",
        " -Direct Plan - Growth Option",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)] + _PLAN_SUFFIX
            break
    return name


def _ensure_benchmarks(session: Session, universe: Universe) -> None:
    for b in universe.benchmarks:
        existing = session.get(Benchmark, b.id)
        if existing is None:
            session.add(Benchmark(id=b.id, name=b.name, yf_ticker=b.yf_ticker))
        else:
            existing.name = b.name
            existing.yf_ticker = b.yf_ticker
    session.flush()


def _store_scheme(session: Session, spec: FundSpec, data: SchemeData) -> tuple[int, ValidationReport]:
    cleaned, report = validate_series((r.date, r.nav) for r in data.rows)

    # Upsert fund row (metadata). amc = fund_house from mfapi.
    fund = session.get(Fund, spec.scheme_code)
    if fund is None:
        fund = Fund(scheme_code=spec.scheme_code)
        session.add(fund)
    fund.name = _canonical_fund_name(data.scheme_name)
    fund.amc = data.fund_house
    fund.category = spec.category
    fund.plan = "Direct-Growth"
    fund.benchmark_id = spec.benchmark_id
    session.flush()

    rows = [{"scheme_code": spec.scheme_code, "date": d, "nav": v} for d, v in cleaned]
    inserted = _upsert_rows(session, NavHistory.__table__, rows, ["scheme_code", "date"])
    return inserted, report


def _store_benchmark(session: Session, benchmark_id: str, rows: list[tuple]) -> int:
    cleaned, _ = validate_series(rows)
    payload = [{"benchmark_id": benchmark_id, "date": d, "close": v} for d, v in cleaned]
    return _upsert_rows(session, BenchmarkHistory.__table__, payload, ["benchmark_id", "date"])


def ingest_universe(universe: Optional[Universe] = None) -> RunResult:
    """Fetch and store every fund + benchmark in the universe, idempotently."""
    configure_logging()
    settings = get_settings()
    uni = universe or load_universe()
    result = RunResult()
    run_id: int | None = None

    # Open an ingestion_run row up front so even a crash leaves an audit trail.
    with session_scope() as s:
        _ensure_benchmarks(s, uni)
        run = IngestionRun(status="running")
        s.add(run)
        s.flush()
        run_id = run.id

    # ---------------- Fund NAVs (parallel fetch) ----------------
    specs = {f.scheme_code: f for f in uni.funds}
    scheme_data: dict[int, SchemeData] = {}
    with MfApiClient() as client:
        with ThreadPoolExecutor(max_workers=max(1, settings.ingest_max_workers)) as ex:
            futures = {ex.submit(client.fetch_scheme, code): code for code in specs}
            for fut in as_completed(futures):
                code = futures[fut]
                try:
                    scheme_data[code] = fut.result()
                except MfApiError as e:
                    result.errors.append(f"scheme {code}: {e}")
                except Exception as e:  # noqa: BLE001
                    result.errors.append(f"scheme {code}: {type(e).__name__}: {e}")

    with session_scope() as s:
        for code, spec in specs.items():
            data = scheme_data.get(code)
            if data is None:
                continue
            try:
                inserted, report = _store_scheme(s, spec, data)
            except Exception as e:  # noqa: BLE001
                result.errors.append(f"store scheme {code}: {type(e).__name__}: {e}")
                continue
            result.rows_inserted += inserted
            result.funds_processed += 1
            if report.has_issues:
                result.warnings.append(f"{code} ({data.scheme_name}): {report.summary()}")

    # ---------------- Benchmarks ----------------
    for b in uni.benchmarks:
        if not b.yf_ticker:
            result.warnings.append(f"benchmark {b.id}: no yf_ticker, skipped")
            continue
        try:
            rows = fetch_benchmark_history(b.yf_ticker)
        except Exception as e:  # noqa: BLE001
            result.errors.append(f"benchmark {b.id}: {type(e).__name__}: {e}")
            continue
        if not rows:
            result.warnings.append(f"benchmark {b.id}: empty history")
            continue
        with session_scope() as s:
            inserted = _store_benchmark(s, b.id, [(r.date, r.close) for r in rows])
        result.rows_inserted += inserted
        result.benchmarks_processed += 1

    # ---------------- Finalise run ----------------
    with session_scope() as s:
        run = s.get(IngestionRun, run_id)
        if run is not None:
            run.finished_at = datetime.now(timezone.utc)
            run.status = "failed" if result.errors else "success"
            run.rows_inserted = result.rows_inserted
            run.funds_processed = result.funds_processed
            run.benchmarks_processed = result.benchmarks_processed
            run.errors = json.dumps(result.errors)[:4000] if result.errors else None
            run.warnings = json.dumps(result.warnings)[:8000] if result.warnings else None

    return result
