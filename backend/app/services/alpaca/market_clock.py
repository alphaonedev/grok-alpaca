"""Alpaca market clock."""

from __future__ import annotations

import httpx

from app.core.config import get_settings

_BASE = "https://api.alpaca.markets"


async def get_clock() -> dict:
    s = get_settings()
    headers = {
        "APCA-API-KEY-ID": s.alpaca_api_key.get_secret_value(),
        "APCA-API-SECRET-KEY": s.alpaca_secret_key.get_secret_value(),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{_BASE}/v2/clock", headers=headers)
        r.raise_for_status()
        return r.json()
