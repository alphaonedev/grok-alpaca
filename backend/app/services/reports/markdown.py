"""Markdown report builder."""

from __future__ import annotations

from io import StringIO


def build_markdown(title: str, sections: list[dict]) -> str:
    buf = StringIO()
    buf.write(f"# {title}\n\n")
    for sec in sections:
        buf.write(f"## {sec.get('heading', '')}\n\n")
        if sec.get("markdown"):
            buf.write(sec["markdown"] + "\n\n")
        if sec.get("table"):
            buf.write(_render_table(sec["table"]) + "\n\n")
        if sec.get("chart_spec"):
            spec = sec["chart_spec"]
            buf.write(f"_[chart: {spec.get('title') or spec.get('kind')}]_\n\n")
    return buf.getvalue()


def _render_table(rows: list[dict]) -> str:
    if not rows:
        return ""
    cols = list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)
