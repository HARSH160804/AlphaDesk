"""Public entry point for the reports module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from reports.context import ReportContext, build_single_fund_context
from reports.docx_report import build_docx
from reports.pptx_report import build_pptx


Format = Literal["pptx", "docx"]
Period = Literal["1Y", "3Y", "5Y", "SI"]


@dataclass
class ReportResult:
    filename: str
    content_type: str
    body: bytes


def generate_report(
    session: Session,
    codes: list[int],
    fmt: Format,
    period: Period = "3Y",
) -> ReportResult:
    """Produce a single report file. The first code is the subject fund.

    Multi-fund comparison reports are a planned extension; for now, when
    multiple codes come in, the first fund is treated as the subject and
    the remaining codes are listed in the peer ranking section.
    """
    if not codes:
        raise ValueError("codes must contain at least one scheme_code")
    subject = codes[0]
    ctx = build_single_fund_context(session, subject, period=period)

    if fmt == "pptx":
        body = build_pptx(ctx)
        filename = _filename(ctx, "pptx")
        return ReportResult(
            filename=filename,
            content_type=(
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ),
            body=body,
        )
    if fmt == "docx":
        body = build_docx(ctx)
        filename = _filename(ctx, "docx")
        return ReportResult(
            filename=filename,
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            body=body,
        )
    raise ValueError(f"unsupported format: {fmt}")


def _filename(ctx: ReportContext, ext: str) -> str:
    safe = (
        ctx.display_name.replace(" ", "_")
        .replace("/", "-")
        .replace(":", "-")
        .replace("·", "")
    )
    # keep short so viewers don't truncate it
    short = "".join(c for c in safe if c.isalnum() or c in ("_", "-"))[:60]
    return f"AlphaDesk-{short}-{ctx.as_of:%Y%m%d}.{ext}"
