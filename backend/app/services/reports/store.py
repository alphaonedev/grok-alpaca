"""Report artifact store. Materializes reports to disk and tracks metadata."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("reports.store")

_LOCK = asyncio.Lock()
ReportFormat = Literal["md", "html", "pdf", "xlsx", "pptx"]


def _root() -> Path:
    s = get_settings()
    p = s.data_dir / "reports"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_path() -> Path:
    return _root() / "index.json"


def _load_index() -> list[dict]:
    p = _index_path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except Exception:
        return []


def _write_index(records: list[dict]) -> None:
    _index_path().write_text(json.dumps(records, indent=2, default=str))


async def save_report(*, title: str, format: ReportFormat, sections: list[dict]) -> dict:
    rid = uuid.uuid4().hex[:12]
    created = datetime.now(timezone.utc).isoformat()
    ext = format if format != "md" else "md"
    filename = f"{rid}.{ext}"
    path = _root() / filename

    payload = {"title": title, "sections": sections, "id": rid, "created_at": created}
    try:
        if format == "md":
            from app.services.reports.markdown import build_markdown

            path.write_text(build_markdown(title, sections))
        elif format == "html":
            from app.services.reports.html_artifact import build_html

            path.write_text(build_html(title, sections))
        elif format == "pdf":
            from app.services.reports.pdf_export import build_pdf

            await asyncio.to_thread(build_pdf, path, title, sections)
        elif format == "xlsx":
            from app.services.reports.xlsx_export import build_xlsx

            await asyncio.to_thread(build_xlsx, path, title, sections)
        elif format == "pptx":
            from app.services.reports.pptx_export import build_pptx

            await asyncio.to_thread(build_pptx, path, title, sections)
        else:  # pragma: no cover
            raise ValueError(f"unknown format {format!r}")
    except Exception as exc:  # noqa: BLE001
        log.exception("report.build_failed", id=rid, format=format, error=str(exc))
        raise

    record = {
        "id": rid,
        "title": title,
        "format": format,
        "filename": filename,
        "created_at": created,
        "url": f"/api/v1/reports/{rid}",
    }

    async with _LOCK:
        records = _load_index()
        records.insert(0, record)
        _write_index(records[:500])

    log.info("report.saved", id=rid, format=format, title=title)
    return record


def list_reports() -> list[dict]:
    return _load_index()


def get_report_path(rid: str) -> Path | None:
    for rec in _load_index():
        if rec["id"] == rid:
            return _root() / rec["filename"]
    return None


def get_report_meta(rid: str) -> dict | None:
    for rec in _load_index():
        if rec["id"] == rid:
            return rec
    return None
