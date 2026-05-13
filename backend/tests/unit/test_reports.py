import asyncio

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_markdown_report():
    from app.services.reports import store

    async def go():
        rec = await store.save_report(
            title="t",
            format="md",
            sections=[{"heading": "h", "markdown": "**hi**"}],
        )
        assert rec["format"] == "md"
        path = store.get_report_path(rec["id"])
        assert path.read_text().startswith("# t")

    asyncio.run(go())


def test_html_report_self_contained():
    from app.services.reports import store

    async def go():
        rec = await store.save_report(
            title="t",
            format="html",
            sections=[{"heading": "h", "markdown": "**hi**", "chart_spec": {"kind": "candle", "bars": []}}],
        )
        path = store.get_report_path(rec["id"])
        html = path.read_text()
        assert "<title>t</title>" in html
        assert "plotly" in html.lower()

    asyncio.run(go())
