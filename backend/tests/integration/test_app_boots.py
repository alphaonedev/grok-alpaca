"""Smoke test: the app boots and /healthz responds."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_healthz():
    from app.main import app

    async def go():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/healthz")
            assert r.status_code == 200
            assert r.json()["ok"] is True

    asyncio.run(go())


def test_openapi_renders():
    from app.main import app

    spec = app.openapi()
    paths = spec["paths"]
    assert "/healthz" in paths
    assert "/api/v1/chat" in paths
    assert "/api/v1/market/bars" in paths
    assert "/api/v1/reports" in paths
