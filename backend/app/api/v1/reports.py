"""Report endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.reports import store

router = APIRouter()


class ReportSection(BaseModel):
    heading: str
    markdown: str | None = None
    chart_spec: dict | None = None
    table: list[dict] | None = None


class CreateReportBody(BaseModel):
    format: Literal["md", "html", "pdf", "xlsx", "pptx"]
    title: str
    sections: list[ReportSection]


@router.post("")
async def create_report(body: CreateReportBody) -> dict:
    record = await store.save_report(
        title=body.title,
        format=body.format,
        sections=[s.model_dump() for s in body.sections],
    )
    return record


@router.get("")
async def list_reports() -> dict:
    return {"reports": store.list_reports()}


@router.get("/{rid}")
async def get_report(rid: str) -> FileResponse:
    meta = store.get_report_meta(rid)
    if not meta:
        raise HTTPException(404, "report not found")
    path = store.get_report_path(rid)
    if path is None or not path.exists():
        raise HTTPException(404, "report file missing")
    media = {
        "md": "text/markdown",
        "html": "text/html",
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }[meta["format"]]
    return FileResponse(str(path), media_type=media, filename=meta["filename"])
