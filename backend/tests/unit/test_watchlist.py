import asyncio
import json
import os
import shutil
from pathlib import Path

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_watchlist_materializes():
    from app.services import watchlist as wl

    async def go():
        lists = await wl.list_watchlists()
        assert any(w["name"] == "Default" for w in lists)
        d = next(w for w in lists if w["name"] == "Default")
        assert "AAPL" in d["symbols"]

    asyncio.run(go())


def test_add_remove_symbol():
    from app.services import watchlist as wl

    async def go():
        await wl.add_symbol("Default", "PLTR")
        w = await wl.get_watchlist("Default")
        assert "PLTR" in w["symbols"]
        await wl.remove_symbol("Default", "PLTR")
        w = await wl.get_watchlist("Default")
        assert "PLTR" not in w["symbols"]

    asyncio.run(go())
