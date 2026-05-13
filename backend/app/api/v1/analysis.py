"""Analysis endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.alpaca import historical as hist
from app.services.analysis import backtest as bt
from app.services.analysis import indicators as ind
from app.services.analysis import screeners
from app.services.analysis import stats as st

router = APIRouter()


class IndicatorsBody(BaseModel):
    symbol: str
    timeframe: str = "1Day"
    lookback: str = "180d"
    indicators: list[str]
    params: dict[str, Any] = Field(default_factory=dict)


@router.post("/indicators")
async def post_indicators(body: IndicatorsBody) -> dict:
    df = await hist.get_bars(body.symbol, timeframe=body.timeframe, lookback=body.lookback)
    if df.empty:
        return {"symbol": body.symbol, "rows": []}
    enriched = ind.compute(df, body.indicators, body.params)
    return {"symbol": body.symbol, "rows": hist.bars_to_records(enriched)}


class StatsBody(BaseModel):
    symbol: str
    lookback: str = "1y"
    benchmark: str | None = "SPY"


@router.post("/stats")
async def post_stats(body: StatsBody) -> dict:
    df = await hist.get_bars(body.symbol, timeframe="1Day", lookback=body.lookback)
    if df.empty:
        return {"symbol": body.symbol, "error": "no bars"}
    r = st.returns(df["close"].astype(float))
    bench = None
    if body.benchmark:
        bdf = await hist.get_bars(body.benchmark, timeframe="1Day", lookback=body.lookback)
        if not bdf.empty:
            bench = st.returns(bdf["close"].astype(float))
    return {"symbol": body.symbol, **st.summary(r, bench)}


class ScreenBody(BaseModel):
    strategy: Literal["momentum", "mean_reversion", "breakout", "overbought", "oversold"]
    universe: list[str] | None = None
    lookback: str = "180d"
    timeframe: str = "1Day"


@router.post("/screen")
async def post_screen(body: ScreenBody) -> dict:
    universe = body.universe or ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "AMZN", "TSLA"]
    bars_by_sym: dict = {}
    for s in universe:
        df = await hist.get_bars(s, timeframe=body.timeframe, lookback=body.lookback)
        if not df.empty:
            bars_by_sym[s] = df
    if body.strategy == "momentum":
        results = screeners.momentum(bars_by_sym)
    elif body.strategy == "mean_reversion":
        results = screeners.mean_reversion(bars_by_sym)
    elif body.strategy == "breakout":
        results = screeners.breakout(bars_by_sym)
    elif body.strategy == "overbought":
        results = [(s, 1.0) for s in screeners.overbought(bars_by_sym)]
    elif body.strategy == "oversold":
        results = [(s, 1.0) for s in screeners.oversold(bars_by_sym)]
    return {"strategy": body.strategy, "results": results[:50]}


class BacktestBody(BaseModel):
    symbol: str
    lookback: str = "2y"
    signal_rule: Literal["sma_cross", "rsi_oversold"] = "sma_cross"
    fast: int = 20
    slow: int = 50
    rsi_length: int = 14
    rsi_threshold: float = 30.0


@router.post("/backtest")
async def post_backtest(body: BacktestBody) -> dict:
    df = await hist.get_bars(body.symbol, timeframe="1Day", lookback=body.lookback)
    if df.empty:
        return {"error": "no bars"}
    close = df["close"].astype(float)
    if body.signal_rule == "sma_cross":
        signal = (ind.sma(close, body.fast) > ind.sma(close, body.slow)).astype(int)
    else:
        signal = (ind.rsi(close, body.rsi_length) < body.rsi_threshold).astype(int)
    result = bt.backtest_signal(close, signal)
    return result.to_dict()
