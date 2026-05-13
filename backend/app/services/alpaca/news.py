"""Alpaca news client wrapper."""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any

from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

from app.core.config import get_settings
from app.services.alpaca._lookback import resolve_window


@lru_cache(maxsize=1)
def get_news_client() -> NewsClient:
    s = get_settings()
    return NewsClient(
        api_key=s.alpaca_api_key.get_secret_value(),
        secret_key=s.alpaca_secret_key.get_secret_value(),
    )


async def get_news(
    symbol: str | list[str] | None = None,
    lookback: str = "7d",
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    symbols = None
    if symbol is not None:
        symbols = [symbol] if isinstance(symbol, str) else list(symbol)
    start_dt, end_dt = resolve_window(lookback, start, end)
    req = NewsRequest(symbols=symbols, start=start_dt, end=end_dt, limit=limit)
    client = get_news_client()
    resp = await asyncio.to_thread(client.get_news, req)
    out = []
    for n in resp.data.get("news", []) if hasattr(resp, "data") else resp.news:  # type: ignore
        out.append(
            {
                "id": n.id,
                "headline": n.headline,
                "author": n.author,
                "summary": n.summary,
                "url": n.url,
                "source": n.source,
                "symbols": n.symbols,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
            }
        )
    return out
