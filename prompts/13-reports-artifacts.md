# Prompt 13 — Reports + artifacts (md / html / xlsx / pdf / pptx)

## Goal
Implement `make_report` and `make_chart` end-to-end. Generated artifacts persist under `~/.grok-alpaca/reports/`, served by FastAPI, viewable/downloadable from the UI.

**Build-time guidance**: invoke the `xlsx`, `pdf`, and `pptx` Anthropic skills when designing each export — they document the underlying library idioms cleanly.

## Tasks
1. `backend/app/services/reports/chart_spec.py`
   - Pydantic discriminated union: `ChartSpec = CandleSpec | LineSpec | IndicatorOverlaySpec | PerformanceSpec | HeatmapSpec`.
   - `CandleSpec(bars, overlays?, subplots?)`, `LineSpec(series)`, etc.

2. `backend/app/services/reports/markdown.py`
   - `render_markdown(md, title=None)` returns inline markdown (no file write; rendered in chat).
   - Optional shortcut to write a `.md` artifact when called via `make_report`.

3. `backend/app/services/reports/html_artifact.py`
   - Jinja2 template `templates/report.html.j2`: self-contained HTML with embedded JSON chart specs + a tiny inline script that renders them with Plotly/Lightweight Charts via CDN.
   - Sandbox-safe: no external network beyond CDN; no cookies.

4. `backend/app/services/reports/xlsx_export.py`
   - `openpyxl`. Build a workbook with sheets: `Summary`, `OHLC`, `Indicators`, `Trades` (if any). Auto-width columns. Conditional formatting for positive/negative columns.

5. `backend/app/services/reports/pdf_export.py`
   - `weasyprint`. Jinja2 template `templates/report.pdf.j2` (clean, professional, mirrors the `pdf` skill's aesthetic). Embed chart images by exporting Plotly figures to PNG.

6. `backend/app/services/reports/pptx_export.py`
   - `python-pptx`. One template: title slide, exec summary, chart slides (one per chart_spec), key metrics, disclaimer.

7. `backend/app/services/reports/store.py`
   - On-disk registry. `save_report(meta, payload, format) -> id`. `get_report(id) -> path`. `list_reports() -> list[meta]`.

8. `backend/app/api/v1/reports.py`
   - From Prompt 07, now backed by the registry.

9. Frontend: `src/components/reports/ReportsList.tsx`
   - Cards with thumbnail (icon by format), title, created_at, download + preview buttons.
   - Preview opens HTML reports in `<ArtifactFrame>`, PDFs in a new tab, xlsx/pptx download directly.

## Acceptance
- `make_report(format="pdf", title="NVDA one-pager", sections=[...])` produces a downloadable PDF.
- `make_report(format="html", ...)` is rendered inline in the chat via `ArtifactFrame`.
- All formats listed in `/api/v1/reports` and openable from the Reports tab.
