"""SQLAlchemy ORM models for AlphaDesk.

Schema
------
- benchmarks        reference table of market/category benchmarks
- funds             scheme-level metadata, FK -> benchmarks
- nav_history       daily NAV per fund (scheme_code, date) is unique
- benchmark_history daily close per benchmark (benchmark_id, date) is unique
- ingestion_runs    one row per orchestrated ingestion attempt
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    yf_ticker: Mapped[Optional[str]] = mapped_column(String(64))

    funds: Mapped[list["Fund"]] = relationship(back_populates="benchmark")
    history: Mapped[list["BenchmarkHistory"]] = relationship(
        back_populates="benchmark",
        cascade="all, delete-orphan",
    )


class Fund(Base):
    __tablename__ = "funds"

    scheme_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    amc: Mapped[Optional[str]] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(64), nullable=False, default="Direct-Growth")
    benchmark_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("benchmarks.id", ondelete="SET NULL"),
        index=True,
    )

    benchmark: Mapped[Optional["Benchmark"]] = relationship(back_populates="funds")
    navs: Mapped[list["NavHistory"]] = relationship(
        back_populates="fund",
        cascade="all, delete-orphan",
    )


class NavHistory(Base):
    __tablename__ = "nav_history"
    __table_args__ = (
        UniqueConstraint("scheme_code", "date", name="uq_nav_scheme_date"),
        CheckConstraint("nav > 0", name="ck_nav_positive"),
        Index("ix_nav_scheme_date", "scheme_code", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scheme_code: Mapped[int] = mapped_column(
        ForeignKey("funds.scheme_code", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    nav: Mapped[float] = mapped_column(Float, nullable=False)

    fund: Mapped["Fund"] = relationship(back_populates="navs")


class BenchmarkHistory(Base):
    __tablename__ = "benchmark_history"
    __table_args__ = (
        UniqueConstraint("benchmark_id", "date", name="uq_bench_date"),
        CheckConstraint("close > 0", name="ck_bench_positive"),
        Index("ix_bench_date", "benchmark_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_id: Mapped[str] = mapped_column(
        ForeignKey("benchmarks.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)

    benchmark: Mapped["Benchmark"] = relationship(back_populates="history")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    rows_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    funds_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    benchmarks_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[Optional[str]] = mapped_column(String(4096))
    warnings: Mapped[Optional[str]] = mapped_column(String(8192))
