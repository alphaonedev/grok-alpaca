"""Alpaca historical market data — crypto. Read-only.

Crypto endpoints don't strictly require API keys, but we pass them through from
settings for parity with the stocks/options clients (and to keep rate limits
attached to our account).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any

import pandas as pd
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoLatestQuoteRequest,
    CryptoLatestTradeRequest,
)

from app.core.config import get_settings
from app.services.alpaca._lookback import resolve_window
from app.services.alpaca.historical import parse_timeframe


@lru_cache(maxsize=1)
def get_client() -> CryptoHistoricalDataClient:
    s = get_settings()
    return CryptoHistoricalDataClient(
        api_key=s.alpaca_api_key.get_secret_value() or None,
        secret_key=s.alpaca_secret_key.get_secret_value() or None,
    )


async def get_crypto_bars(
    symbol: str,
    timeframe: str = "1Day",
    lookback: str = "90d",
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    start_dt, end_dt = resolve_window(lookback, start, end)
    req = CryptoBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=parse_timeframe(timeframe),
        start=start_dt,
        end=end_dt,
        limit=limit,
    )
    client = get_client()
    bars = await asyncio.to_thread(client.get_crypto_bars, req)
    df = bars.df  # type: ignore[union-attr]
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)
    return df


async def get_crypto_latest_quote(symbol: str) -> dict[str, Any]:
    req = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
    client = get_client()
    resp = await asyncio.to_thread(client.get_crypto_latest_quote, req)
    q = resp[symbol]
    return {
        "symbol": symbol,
        "ask_price": getattr(q, "ask_price", None),
        "ask_size": getattr(q, "ask_size", None),
        "bid_price": getattr(q, "bid_price", None),
        "bid_size": getattr(q, "bid_size", None),
        "timestamp": q.timestamp.isoformat() if getattr(q, "timestamp", None) else None,
    }


async def get_crypto_latest_trade(symbol: str) -> dict[str, Any]:
    req = CryptoLatestTradeRequest(symbol_or_symbols=symbol)
    client = get_client()
    resp = await asyncio.to_thread(client.get_crypto_latest_trade, req)
    t = resp[symbol]
    return {
        "symbol": symbol,
        "price": getattr(t, "price", None),
        "size": getattr(t, "size", None),
        "timestamp": t.timestamp.isoformat() if getattr(t, "timestamp", None) else None,
    }
