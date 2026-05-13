"""Persistent watchlist storage."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.config import get_settings

_LOCK = asyncio.Lock()

DEFAULT_WATCHLIST = {
    "name": "Default",
    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "AMZN", "TSLA"],
}


def _path() -> Path:
    return get_settings().data_dir / "watchlist.json"


def _ensure() -> list[dict]:
    p = _path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps([DEFAULT_WATCHLIST]))
    try:
        return json.loads(p.read_text())
    except Exception:
        p.write_text(json.dumps([DEFAULT_WATCHLIST]))
        return [DEFAULT_WATCHLIST]


def _write(records: list[dict]) -> None:
    _path().write_text(json.dumps(records, indent=2))


async def list_watchlists() -> list[dict]:
    async with _LOCK:
        return _ensure()


async def get_watchlist(name: str) -> dict | None:
    async with _LOCK:
        for w in _ensure():
            if w["name"] == name:
                return w
        return None


async def create_watchlist(name: str, symbols: list[str]) -> dict:
    async with _LOCK:
        items = _ensure()
        if any(w["name"] == name for w in items):
            raise ValueError(f"watchlist {name!r} already exists")
        item = {"name": name, "symbols": list(dict.fromkeys(symbols))}
        items.append(item)
        _write(items)
        return item


async def delete_watchlist(name: str) -> None:
    async with _LOCK:
        items = [w for w in _ensure() if w["name"] != name]
        _write(items)


async def add_symbol(name: str, symbol: str) -> dict:
    async with _LOCK:
        items = _ensure()
        for w in items:
            if w["name"] == name:
                if symbol not in w["symbols"]:
                    w["symbols"].append(symbol)
                _write(items)
                return w
        raise KeyError(name)


async def remove_symbol(name: str, symbol: str) -> dict:
    async with _LOCK:
        items = _ensure()
        for w in items:
            if w["name"] == name:
                w["symbols"] = [s for s in w["symbols"] if s != symbol]
                _write(items)
                return w
        raise KeyError(name)
