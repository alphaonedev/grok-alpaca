"""Alpaca historical market data — stocks. Read-only."""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import lru_cache
from typing import Any

import pandas as pd
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockSnapshotRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from app.core.config import get_settings
from app.services.alpaca._lookback import resolve_window

_TIMEFRAMES: dict[str, TimeFrame] = {
    "1Min": TimeFrame(1, TimeFrameUnit.Minute),
    "5Min": TimeFrame(5, TimeFrameUnit.Minute),
    "15Min": TimeFrame(15, TimeFrameUnit.Minute),
    "30Min": TimeFrame(30, TimeFrameUnit.Minute),
    "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
    "1Day": TimeFrame(1, TimeFrameUnit.Day),
    "1Week": TimeFrame(1, TimeFrameUnit.Week),
    "1Month": TimeFrame(1, TimeFrameUnit.Month),
}


def parse_timeframe(s: str) -> TimeFrame:
    if s not in _TIMEFRAMES:
        raise ValueError(f"unknown timeframe {s!r}; one of {list(_TIMEFRAMES)}")
    return _TIMEFRAMES[s]


@lru_cache(maxsize=1)
def get_client() -> StockHistoricalDataClient:
    s = get_settings()
    return StockHistoricalDataClient(
        api_key=s.alpaca_api_key.get_secret_value(),
        secret_key=s.alpaca_secret_key.get_secret_value(),
    )


async def get_bars(
    symbol: str | list[str],
    timeframe: str = "1Day",
    lookback: str | None = "30d",
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    symbols = [symbol] if isinstance(symbol, str) else list(symbol)
    start_dt, end_dt = resolve_window(lookback, start, end)
    req = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=parse_timeframe(timeframe),
        start=start_dt,
        end=end_dt,
        limit=limit,
    )
    client = get_client()
    bars = await asyncio.to_thread(client.get_stock_bars, req)
    df = bars.df  # type: ignore[union-attr]
    if df is None or df.empty:
        return pd.DataFrame()
    # Multi-index (symbol, timestamp) → flatten for the single-symbol common case
    if isinstance(df.index, pd.MultiIndex) and len(symbols) == 1:
        df = df.reset_index(level=0, drop=True)
    return df


async def get_latest_quote(symbol: str) -> dict[str, Any]:
    req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
    client = get_client()
    resp = await asyncio.to_thread(client.get_stock_latest_quote, req)
    q = resp[symbol]
    return {
        "symbol": symbol,
        "ask_price": q.ask_price,
        "ask_size": q.ask_size,
        "bid_price": q.bid_price,
        "bid_size": q.bid_size,
        "timestamp": q.timestamp.isoformat() if q.timestamp else None,
    }


async def get_latest_trade(symbol: str) -> dict[str, Any]:
    req = StockLatestTradeRequest(symbol_or_symbols=symbol)
    client = get_client()
    resp = await asyncio.to_thread(client.get_stock_latest_trade, req)
    t = resp[symbol]
    return {
        "symbol": symbol,
        "price": t.price,
        "size": t.size,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
    }


async def get_snapshot(symbol: str | list[str]) -> dict[str, Any]:
    symbols = [symbol] if isinstance(symbol, str) else list(symbol)
    req = StockSnapshotRequest(symbol_or_symbols=symbols)
    client = get_client()
    resp = await asyncio.to_thread(client.get_stock_snapshot, req)
    out: dict[str, Any] = {}
    for sym, snap in resp.items():
        out[sym] = {
            "latest_trade": _trade_dict(snap.latest_trade) if snap.latest_trade else None,
            "latest_quote": _quote_dict(snap.latest_quote) if snap.latest_quote else None,
            "minute_bar": _bar_dict(snap.minute_bar) if snap.minute_bar else None,
            "daily_bar": _bar_dict(snap.daily_bar) if snap.daily_bar else None,
            "previous_daily_bar": _bar_dict(snap.previous_daily_bar)
            if snap.previous_daily_bar
            else None,
        }
    return out


def _trade_dict(t) -> dict:
    return {"price": t.price, "size": t.size, "timestamp": t.timestamp.isoformat()}


def _quote_dict(q) -> dict:
    return {
        "ask_price": q.ask_price,
        "ask_size": q.ask_size,
        "bid_price": q.bid_price,
        "bid_size": q.bid_size,
        "timestamp": q.timestamp.isoformat(),
    }


def _bar_dict(b) -> dict:
    return {
        "open": b.open,
        "high": b.high,
        "low": b.low,
        "close": b.close,
        "volume": b.volume,
        "vwap": b.vwap,
        "trade_count": b.trade_count,
        "timestamp": b.timestamp.isoformat(),
    }


def bars_to_records(df: pd.DataFrame) -> list[dict]:
    """JSON-ready records, with ISO-8601 timestamps."""
    if df.empty:
        return []
    out = df.reset_index().copy()
    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True).dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    return out.to_dict(orient="records")
