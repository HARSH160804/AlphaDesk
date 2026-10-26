"""`/api/reports` — generate a PPTX or DOCX client report."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas import ReportRequest
from reports.context import build_single_fund_context
from reports.generator import generate_report


router = APIRouter(prefix="/api/reports", tags=["reports"])

# The outline the UI preview reflects — stays in sync with pptx_report.py.
OUTLINE = [
    {"n": 1,  "title": "Title",                   "body": "Fund name, AMC, benchmark, window"},
    {"n": 2,  "title": "Executive summary",       "body": "Three takeaways generated from the data"},
    {"n": 3,  "title": "Performance vs benchmark","body": "Rebased line chart"},
    {"n": 4,  "title": "Trailing returns",        "body": "1M–5Y table + risk summary"},
    {"n": 5,  "title": "Calendar-year returns",   "body": "Fund vs benchmark grouped bars"},
    {"n": 6,  "title": "Risk metrics",            "body": "β · α · vol · Sharpe · Sortino · TE · IR"},
    {"n": 7,  "title": "Drawdown chart",          "body": "Peak-to-current with worst-episode annotation"},
    {"n": 8,  "title": "Rolling 3Y CAGR",         "body": "Consistency across the window"},
    {"n": 9,  "title": "Peer ranking",            "body": "In-category leaderboard; subject fund flagged"},
    {"n": 10, "title": "Methodology & disclaimer","body": "Formulas, data sources, legal"},
]


@router.get("/outline", summary="Fixed 10-section outline the deck will produce")
def outline() -> dict:
    return {"slides": OUTLINE}


@router.post(
    "",
    summary="Generate a PPTX or DOCX client report",
    responses={
        200: {
            "description": "Binary report file",
            "content": {
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": {},
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document":    {},
            },
        },
        404: {"description": "Fund not found"},
    },
)
def generate(req: ReportRequest) -> Response:
    try:
        with SessionLocal() as session:  # type: Session
            result = generate_report(
                session=session,
                codes=req.codes,
                fmt=req.format,
                period=req.period,
            )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=result.body,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Report-Filename": result.filename,
            "Access-Control-Expose-Headers": "Content-Disposition, X-Report-Filename",
        },
    )


@router.get(
    "/preview",
    summary="Preview the outline + takeaways for a fund, no file generation",
)
def preview(
    codes: str = Query(..., pattern=r"^[0-9]+(,[0-9]+)*$"),
    period: str = Query("3Y"),
) -> dict:
    code_list = [int(c) for c in codes.split(",") if c]
    if not code_list:
        raise HTTPException(400, "no scheme codes provided")
    try:
        with SessionLocal() as session:
            ctx = build_single_fund_context(session, code_list[0], period=period)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "fund": {
            "scheme_code": ctx.fund.scheme_code,
            "name": ctx.display_name,
            "benchmark_id": ctx.fund.benchmark_id,
            "as_of": ctx.as_of.isoformat(),
        },
        "takeaways": ctx.takeaways,
        "outline": OUTLINE,
    }
