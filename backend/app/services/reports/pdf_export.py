"""PDF export — weasyprint over the HTML artifact template."""

from __future__ import annotations

from pathlib import Path

from app.services.reports.html_artifact import build_html


def build_pdf(path: Path, title: str, sections: list[dict]) -> None:
    html_content = build_html(title, sections)
    try:
        from weasyprint import HTML  # heavy import; defer

        HTML(string=html_content).write_pdf(target=str(path))
    except Exception as exc:  # noqa: BLE001
        # Fallback: write HTML content with .pdf extension would mislead, so write a sibling .html
        path.with_suffix(".html").write_text(html_content)
        raise RuntimeError(
            f"PDF generation requires weasyprint with its system libraries. "
            f"Wrote HTML fallback alongside. Original error: {exc}"
        ) from exc
