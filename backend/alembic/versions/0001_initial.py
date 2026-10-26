"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-26
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benchmarks",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("yf_ticker", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "funds",
        sa.Column("scheme_code", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("amc", sa.String(length=128), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column(
            "plan",
            sa.String(length=64),
            nullable=False,
            server_default="Direct-Growth",
        ),
        sa.Column(
            "benchmark_id",
            sa.String(length=32),
            sa.ForeignKey("benchmarks.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_funds_category", "funds", ["category"])
    op.create_index("ix_funds_benchmark_id", "funds", ["benchmark_id"])

    op.create_table(
        "nav_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "scheme_code",
            sa.Integer(),
            sa.ForeignKey("funds.scheme_code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("nav", sa.Float(), nullable=False),
        sa.UniqueConstraint("scheme_code", "date", name="uq_nav_scheme_date"),
        sa.CheckConstraint("nav > 0", name="ck_nav_positive"),
    )
    op.create_index("ix_nav_scheme_date", "nav_history", ["scheme_code", "date"])

    op.create_table(
        "benchmark_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "benchmark_id",
            sa.String(length=32),
            sa.ForeignKey("benchmarks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.UniqueConstraint("benchmark_id", "date", name="uq_bench_date"),
        sa.CheckConstraint("close > 0", name="ck_bench_positive"),
    )
    op.create_index("ix_bench_date", "benchmark_history", ["benchmark_id", "date"])

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="running"),
        sa.Column("rows_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funds_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "benchmarks_processed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("errors", sa.String(length=4096), nullable=True),
        sa.Column("warnings", sa.String(length=8192), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_index("ix_bench_date", table_name="benchmark_history")
    op.drop_table("benchmark_history")
    op.drop_index("ix_nav_scheme_date", table_name="nav_history")
    op.drop_table("nav_history")
    op.drop_index("ix_funds_benchmark_id", table_name="funds")
    op.drop_index("ix_funds_category", table_name="funds")
    op.drop_table("funds")
    op.drop_table("benchmarks")
