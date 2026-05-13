"""Market data endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.alpaca import historical as hist
from app.services.alpaca import market_clock, news

router = APIRouter()


@router.get("/bars")
async def get_bars(
    symbol: str = Query(..., description="Ticker symbol"),
    timeframe: str = Query("1Day", description="One of 1Min,5Min,15Min,30Min,1Hour,1Day,1Week,1Month"),
    lookback: str = Query("90d", description="Window like 30d, 6mo, 1y, 5y"),
    limit: int | None = None,
) -> dict[str, Any]:
    df = await hist.get_bars(symbol, timeframe=timeframe, lookback=lookback, limit=limit)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "lookback": lookback,
        "count": int(df.shape[0]),
        "bars": hist.bars_to_records(df),
    }


@router.get("/quote/{symbol}")
async def get_quote(symbol: str) -> dict:
    return await hist.get_latest_quote(symbol)


@router.get("/trade/{symbol}")
async def get_trade(symbol: str) -> dict:
    return await hist.get_latest_trade(symbol)


@router.get("/snapshot/{symbol}")
async def get_snapshot(symbol: str) -> dict:
    snap = await hist.get_snapshot(symbol)
    return snap.get(symbol, {})


@router.get("/clock")
async def get_clock() -> dict:
    try:
        return await market_clock.get_clock()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"upstream clock error: {exc}")


@router.get("/news")
async def get_news(symbol: str | None = None, limit: int = 20, lookback: str = "7d") -> dict:
    items = await news.get_news(symbol=symbol, limit=limit, lookback=lookback)
    return {"count": len(items), "items": items}
