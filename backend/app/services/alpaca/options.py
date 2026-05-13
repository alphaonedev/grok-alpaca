"""Alpaca historical market data — options. Read-only."""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from functools import lru_cache
from typing import Any

import pandas as pd
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import (
    OptionBarsRequest,
    OptionChainRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
)

from app.core.config import get_settings
from app.services.alpaca._lookback import resolve_window
from app.services.alpaca.historical import parse_timeframe


@lru_cache(maxsize=1)
def get_client() -> OptionHistoricalDataClient:
    s = get_settings()
    return OptionHistoricalDataClient(
        api_key=s.alpaca_api_key.get_secret_value(),
        secret_key=s.alpaca_secret_key.get_secret_value(),
    )


def _trade_dict(t) -> dict[str, Any] | None:
    if t is None:
        return None
    return {
        "price": getattr(t, "price", None),
        "size": getattr(t, "size", None),
        "timestamp": t.timestamp.isoformat() if getattr(t, "timestamp", None) else None,
    }


def _quote_dict(q) -> dict[str, Any] | None:
    if q is None:
        return None
    return {
        "ask_price": getattr(q, "ask_price", None),
        "ask_size": getattr(q, "ask_size", None),
        "bid_price": getattr(q, "bid_price", None),
        "bid_size": getattr(q, "bid_size", None),
        "timestamp": q.timestamp.isoformat() if getattr(q, "timestamp", None) else None,
    }


def _greeks_dict(g) -> dict[str, Any] | None:
    if g is None:
        return None
    return {
        "delta": getattr(g, "delta", None),
        "gamma": getattr(g, "gamma", None),
        "rho": getattr(g, "rho", None),
        "theta": getattr(g, "theta", None),
        "vega": getattr(g, "vega", None),
    }


async def get_option_chain(
    underlying: str,
    expiration_date: str | None = None,
) -> dict[str, Any]:
    """Return the option chain for an underlying as JSON-ready dict.

    The Alpaca chain returns a mapping of contract symbol -> OptionsSnapshot
    (latest trade/quote, implied volatility, greeks). open_interest is not part
    of the snapshot payload, so callers should fall back to implied_volatility
    when ranking contracts.
    """
    exp: date | None = None
    if expiration_date:
        exp = datetime.strptime(expiration_date, "%Y-%m-%d").date()
    req = OptionChainRequest(
        underlying_symbol=underlying,
        expiration_date=exp,
    )
    client = get_client()
    resp = await asyncio.to_thread(client.get_option_chain, req)
    out: dict[str, dict[str, Any]] = {}
    # resp is dict[str, OptionsSnapshot]
    for sym, snap in (resp or {}).items():
        out[sym] = {
            "symbol": sym,
            "latest_trade": _trade_dict(getattr(snap, "latest_trade", None)),
            "latest_quote": _quote_dict(getattr(snap, "latest_quote", None)),
            "implied_volatility": getattr(snap, "implied_volatility", None),
            "greeks": _greeks_dict(getattr(snap, "greeks", None)),
        }
    return out


async def get_option_bars(
    symbol: str,
    timeframe: str = "1Day",
    lookback: str = "30d",
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    start_dt, end_dt = resolve_window(lookback, start, end)
    req = OptionBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=parse_timeframe(timeframe),
        start=start_dt,
        end=end_dt,
        limit=limit,
    )
    client = get_client()
    bars = await asyncio.to_thread(client.get_option_bars, req)
    df = bars.df  # type: ignore[union-attr]
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index(level=0, drop=True)
    return df


async def get_option_latest_quote(symbol: str) -> dict[str, Any]:
    req = OptionLatestQuoteRequest(symbol_or_symbols=symbol)
    client = get_client()
    resp = await asyncio.to_thread(client.get_option_latest_quote, req)
    q = resp[symbol]
    return {
        "symbol": symbol,
        "ask_price": getattr(q, "ask_price", None),
        "ask_size": getattr(q, "ask_size", None),
        "bid_price": getattr(q, "bid_price", None),
        "bid_size": getattr(q, "bid_size", None),
        "timestamp": q.timestamp.isoformat() if getattr(q, "timestamp", None) else None,
    }


async def get_option_latest_trade(symbol: str) -> dict[str, Any]:
    req = OptionLatestTradeRequest(symbol_or_symbols=symbol)
    client = get_client()
    resp = await asyncio.to_thread(client.get_option_latest_trade, req)
    t = resp[symbol]
    return {
        "symbol": symbol,
        "price": getattr(t, "price", None),
        "size": getattr(t, "size", None),
        "timestamp": t.timestamp.isoformat() if getattr(t, "timestamp", None) else None,
    }
