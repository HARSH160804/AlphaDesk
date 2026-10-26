"""CLI entry point: `python -m ingestion.cli` runs a full ingest."""
from __future__ import annotations

import logging
import sys

from rich.console import Console
from rich.table import Table

from app.logging_setup import configure_logging
from ingestion.pipeline import ingest_universe

logger = logging.getLogger("ingestion.cli")
console = Console()


def main() -> int:
    configure_logging()
    console.print("[bold]AlphaDesk[/bold] running ingestion...")
    result = ingest_universe()

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_row("rows upserted", f"{result.rows_inserted:,}")
    table.add_row("funds processed", f"{result.funds_processed}")
    table.add_row("benchmarks processed", f"{result.benchmarks_processed}")
    table.add_row("warnings", f"{len(result.warnings)}")
    table.add_row("errors", f"{len(result.errors)}")
    console.print(table)

    if result.warnings:
        console.print("\n[yellow]warnings[/yellow]")
        for w in result.warnings[:20]:
            console.print(f"  - {w}")
        if len(result.warnings) > 20:
            console.print(f"  ... and {len(result.warnings) - 20} more")

    if result.errors:
        console.print("\n[red]errors[/red]")
        for e in result.errors:
            console.print(f"  - {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
