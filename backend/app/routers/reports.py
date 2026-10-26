"""`/api/reports` — stub endpoint. The real PPTX/DOCX generator lands in Phase 7.

Keeping the route live now so the frontend can wire against the final shape.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import ReportRequest


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post(
    "",
    status_code=501,
    summary="Generate a PPTX or DOCX client report (coming in Phase 7)",
    responses={
        501: {"description": "Not yet implemented"},
        400: {"description": "Invalid request"},
    },
)
def generate_report(_: ReportRequest) -> dict:
    raise HTTPException(
        status_code=501,
        detail="report generation lands in Phase 7; request body validated for shape",
    )
