"""Self-contained HTML report builder."""

from __future__ import annotations

import html
import json
from textwrap import dedent


def build_html(title: str, sections: list[dict]) -> str:
    body_parts: list[str] = [f"<h1>{html.escape(title)}</h1>"]
    chart_specs: list[dict] = []
    for i, sec in enumerate(sections):
        body_parts.append(f"<section><h2>{html.escape(sec.get('heading', ''))}</h2>")
        if sec.get("markdown"):
            body_parts.append(f"<div class='md'>{_markdown_to_html(sec['markdown'])}</div>")
        if sec.get("table"):
            body_parts.append(_render_table_html(sec["table"]))
        if sec.get("chart_spec"):
            chart_id = f"chart-{i}"
            chart_specs.append({"id": chart_id, "spec": sec["chart_spec"]})
            body_parts.append(f"<div id='{chart_id}' class='chart'></div>")
        body_parts.append("</section>")

    body = "\n".join(body_parts)
    specs_json = json.dumps(chart_specs)

    return dedent(
        f"""\
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <title>{html.escape(title)}</title>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <!--
            Subresource Integrity (SRI) pin for the Plotly CDN.
            sha384 computed from cdn.plot.ly/plotly-2.35.0.min.js on 2026-05-13.
            If the CDN is ever compromised, the browser will refuse to execute
            the script. See SECURITY.md.
          -->
          <script
            src="https://cdn.plot.ly/plotly-2.35.0.min.js"
            integrity="sha384-TAqBiqItCr14J//ULLD26bSQ8Z6uPnlisSwkvWaqP8SCSiDkgR8jNknuAv8uxSOT"
            crossorigin="anonymous"
            referrerpolicy="no-referrer"></script>
          <style>
            :root {{ color-scheme: dark; }}
            html, body {{ background: #0b1220; color: #e6edf7; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; line-height: 1.55; }}
            body {{ max-width: 960px; margin: 0 auto; padding: 32px 24px 80px; }}
            h1 {{ font-size: 28px; border-bottom: 1px solid #1f2a44; padding-bottom: 12px; }}
            h2 {{ font-size: 20px; margin-top: 32px; color: #8fb6ff; }}
            section {{ margin-bottom: 24px; }}
            .chart {{ width: 100%; height: 420px; background: #0f1828; border-radius: 8px; margin: 8px 0; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
            th, td {{ border: 1px solid #1f2a44; padding: 6px 10px; text-align: left; }}
            th {{ background: #142036; }}
            tr:nth-child(even) td {{ background: #0d1525; }}
            code {{ background: #142036; padding: 2px 6px; border-radius: 4px; }}
          </style>
        </head>
        <body>
          {body}
          <script>
            const specs = {specs_json};
            specs.forEach(({{id, spec}}) => {{
              const el = document.getElementById(id);
              if (!el) return;
              const layout = {{
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {{ color: '#e6edf7' }},
                margin: {{ t: 16, r: 16, b: 32, l: 48 }},
              }};
              if (spec.kind === 'candle' && spec.bars) {{
                Plotly.newPlot(el, [{{
                  type: 'candlestick',
                  x: spec.bars.map(b => b.timestamp),
                  open: spec.bars.map(b => b.open),
                  high: spec.bars.map(b => b.high),
                  low: spec.bars.map(b => b.low),
                  close: spec.bars.map(b => b.close),
                  name: spec.symbol || ''
                }}], layout, {{responsive: true}});
              }} else if (spec.bars && spec.bars.length) {{
                Plotly.newPlot(el, [{{
                  type: 'scatter', mode: 'lines',
                  x: spec.bars.map(b => b.timestamp),
                  y: spec.bars.map(b => b.close),
                  name: spec.symbol || ''
                }}], layout, {{responsive: true}});
              }} else if (spec.series) {{
                Plotly.newPlot(el, spec.series.map(s => ({{
                  type: 'scatter', mode: 'lines',
                  x: s.x, y: s.y, name: s.name
                }})), layout, {{responsive: true}});
              }}
            }});
          </script>
        </body>
        </html>
        """
    )


def _markdown_to_html(md: str) -> str:
    # Best-effort using markdown-it-py if available, else escape + <p>.
    try:
        from markdown_it import MarkdownIt

        return MarkdownIt("gfm-like").render(md)
    except Exception:
        return "<p>" + html.escape(md).replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"


def _render_table_html(rows: list[dict]) -> str:
    if not rows:
        return ""
    cols = list(rows[0].keys())
    head = "<tr>" + "".join(f"<th>{html.escape(str(c))}</th>" for c in cols) + "</tr>"
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(r.get(c, '')))}</td>" for c in cols) + "</tr>"
        for r in rows
    )
    return f"<table>{head}{body}</table>"
