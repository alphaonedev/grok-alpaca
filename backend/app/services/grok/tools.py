"""Tool definitions Grok can call.

Each Tool exposes:
  - name           snake_case identifier
  - description    short text shown to the model
  - args_schema    Pydantic model for arguments
  - run(args)      async coroutine returning a ToolResult

A ToolResult bundles the JSON content fed back to the model with optional
"side effects" that the orchestrator surfaces to the UI as events
(charts, artifacts, etc).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal, Protocol

import pandas as pd
from pydantic import BaseModel, Field

from app.services.alpaca import crypto as alpaca_crypto
from app.services.alpaca import historical as alpaca_hist
from app.services.alpaca import news as alpaca_news
from app.services.alpaca import options as alpaca_options
from app.services.analysis import indicators as ind
from app.services.analysis import screeners
from app.services.analysis import stats as st


# ---------------------------------------------------------------------------
# Side effects + tool result envelope
# ---------------------------------------------------------------------------


class SideEffect(BaseModel):
    type: Literal["chart", "artifact", "markdown"]
    data: dict


@dataclass
class ToolResult:
    content: Any
    side_effects: list[SideEffect] = field(default_factory=list)


class Tool(Protocol):
    name: str
    description: str
    args_schema: type[BaseModel]
    run: Callable[[BaseModel], Awaitable[ToolResult]]


# ---------------------------------------------------------------------------
# Argument schemas
# ---------------------------------------------------------------------------


Timeframe = Literal["1Min", "5Min", "15Min", "30Min", "1Hour", "1Day", "1Week", "1Month"]
IndicatorName = Literal["SMA", "EMA", "RSI", "MACD", "BBANDS", "ATR", "VWAP", "OBV", "STOCH"]


class GetBarsArgs(BaseModel):
    symbol: str
    timeframe: Timeframe = "1Day"
    lookback: str = Field("90d", description="e.g. '30d', '6mo', '1y', '5y'")


class GetQuoteArgs(BaseModel):
    symbol: str


class GetSnapshotArgs(BaseModel):
    symbol: str


class ComputeIndicatorsArgs(BaseModel):
    symbol: str
    timeframe: Timeframe = "1Day"
    lookback: str = "180d"
    indicators: list[IndicatorName]
    params: dict[str, Any] = Field(default_factory=dict)


class ComputeStatsArgs(BaseModel):
    symbol: str
    lookback: str = "1y"
    benchmark: str | None = "SPY"


class GetNewsArgs(BaseModel):
    symbol: str
    limit: int = 20
    lookback: str = "7d"


class ScreenArgs(BaseModel):
    strategy: Literal["momentum", "mean_reversion", "breakout", "overbought", "oversold"]
    universe: list[str] = Field(
        default_factory=lambda: ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "AMZN", "TSLA"]
    )
    lookback: str = "180d"
    timeframe: Timeframe = "1Day"


class ChartSpec(BaseModel):
    kind: Literal["candle", "line", "indicator_overlay", "performance"]
    title: str | None = None
    symbol: str | None = None
    bars: list[dict] | None = None
    series: list[dict] | None = None
    overlays: list[dict] | None = None
    subplots: list[dict] | None = None


class MakeChartArgs(BaseModel):
    chart_spec: ChartSpec


class RenderMarkdownArgs(BaseModel):
    markdown: str
    title: str | None = None


class ReportSection(BaseModel):
    heading: str
    markdown: str | None = None
    chart_spec: ChartSpec | None = None
    table: list[dict] | None = None


class MakeReportArgs(BaseModel):
    format: Literal["html", "pdf", "xlsx", "pptx", "md"]
    title: str
    sections: list[ReportSection]


class GetOptionChainArgs(BaseModel):
    underlying: str = Field(..., description="Underlying ticker, e.g. 'AAPL'")
    expiration_date: str | None = Field(
        None, description="Optional YYYY-MM-DD expiration filter"
    )


class GetCryptoBarsArgs(BaseModel):
    symbol: str = Field(..., description="Crypto pair, e.g. 'BTC/USD'")
    timeframe: Timeframe = "1Day"
    lookback: str = Field("90d", description="e.g. '30d', '6mo', '1y'")


class GetCryptoQuoteArgs(BaseModel):
    symbol: str = Field(..., description="Crypto pair, e.g. 'BTC/USD'")


# ---------------------------------------------------------------------------
# Tool runners
# ---------------------------------------------------------------------------


def _bars_payload(df: pd.DataFrame, symbol: str) -> list[dict]:
    if df.empty:
        return []
    out = df.reset_index().rename(columns={"index": "timestamp"})
    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    keep = [c for c in ("timestamp", "open", "high", "low", "close", "volume", "vwap") if c in out.columns]
    return out[keep].to_dict(orient="records")


async def _run_get_bars(args: GetBarsArgs) -> ToolResult:
    df = await alpaca_hist.get_bars(args.symbol, timeframe=args.timeframe, lookback=args.lookback)
    bars = _bars_payload(df, args.symbol)
    summary = {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "lookback": args.lookback,
        "count": len(bars),
        "first": bars[0] if bars else None,
        "last": bars[-1] if bars else None,
    }
    side = [
        SideEffect(
            type="chart",
            data={
                "kind": "candle",
                "title": f"{args.symbol} {args.timeframe} ({args.lookback})",
                "symbol": args.symbol,
                "bars": bars,
            },
        )
    ]
    return ToolResult(content=summary, side_effects=side)


async def _run_get_quote(args: GetQuoteArgs) -> ToolResult:
    q = await alpaca_hist.get_latest_quote(args.symbol)
    return ToolResult(content=q)


async def _run_get_snapshot(args: GetSnapshotArgs) -> ToolResult:
    snap = await alpaca_hist.get_snapshot(args.symbol)
    return ToolResult(content=snap)


async def _run_compute_indicators(args: ComputeIndicatorsArgs) -> ToolResult:
    df = await alpaca_hist.get_bars(args.symbol, timeframe=args.timeframe, lookback=args.lookback)
    if df.empty:
        return ToolResult(content={"error": "no bars returned", "symbol": args.symbol})
    enriched = ind.compute(df, [str(i) for i in args.indicators], args.params)
    bars = _bars_payload(enriched, args.symbol)
    last_row = enriched.iloc[-1].to_dict()
    side = [
        SideEffect(
            type="chart",
            data={
                "kind": "indicator_overlay",
                "title": f"{args.symbol} {args.timeframe} — {', '.join(args.indicators)}",
                "symbol": args.symbol,
                "bars": bars,
                "overlays": [{"name": i} for i in args.indicators],
            },
        )
    ]
    return ToolResult(
        content={
            "symbol": args.symbol,
            "indicators": list(args.indicators),
            "last_values": {k: (float(v) if isinstance(v, (int, float)) and v == v else None) for k, v in last_row.items()},
            "count": len(bars),
        },
        side_effects=side,
    )


async def _run_compute_stats(args: ComputeStatsArgs) -> ToolResult:
    df = await alpaca_hist.get_bars(args.symbol, timeframe="1Day", lookback=args.lookback)
    if df.empty:
        return ToolResult(content={"error": "no bars returned"})
    r = st.returns(df["close"].astype(float))
    bench = None
    if args.benchmark:
        bdf = await alpaca_hist.get_bars(args.benchmark, timeframe="1Day", lookback=args.lookback)
        if not bdf.empty:
            bench = st.returns(bdf["close"].astype(float))
    return ToolResult(content={"symbol": args.symbol, **st.summary(r, bench)})


async def _run_get_news(args: GetNewsArgs) -> ToolResult:
    items = await alpaca_news.get_news(symbol=args.symbol, limit=args.limit, lookback=args.lookback)
    return ToolResult(content={"symbol": args.symbol, "count": len(items), "items": items[: args.limit]})


async def _run_screen(args: ScreenArgs) -> ToolResult:
    bars_by_sym: dict[str, pd.DataFrame] = {}
    for s in args.universe:
        df = await alpaca_hist.get_bars(s, timeframe=args.timeframe, lookback=args.lookback)
        if not df.empty:
            bars_by_sym[s] = df

    if args.strategy == "momentum":
        ranked = screeners.momentum(bars_by_sym)
    elif args.strategy == "mean_reversion":
        ranked = screeners.mean_reversion(bars_by_sym)
    elif args.strategy == "breakout":
        ranked = screeners.breakout(bars_by_sym)
    elif args.strategy == "overbought":
        ranked = [(s, 1.0) for s in screeners.overbought(bars_by_sym)]
    elif args.strategy == "oversold":
        ranked = [(s, 1.0) for s in screeners.oversold(bars_by_sym)]
    else:  # pragma: no cover
        ranked = []
    return ToolResult(content={"strategy": args.strategy, "results": ranked[:25]})


async def _run_make_chart(args: MakeChartArgs) -> ToolResult:
    return ToolResult(
        content={"ok": True, "kind": args.chart_spec.kind, "title": args.chart_spec.title},
        side_effects=[SideEffect(type="chart", data=args.chart_spec.model_dump())],
    )


async def _run_render_markdown(args: RenderMarkdownArgs) -> ToolResult:
    return ToolResult(
        content={"ok": True, "length": len(args.markdown)},
        side_effects=[SideEffect(type="markdown", data={"title": args.title, "markdown": args.markdown})],
    )


def _contract_sort_key(entry: dict) -> float:
    """Prefer open_interest, fall back to implied_volatility; missing -> -inf."""
    oi = entry.get("open_interest")
    if isinstance(oi, (int, float)):
        return float(oi)
    iv = entry.get("implied_volatility")
    if isinstance(iv, (int, float)):
        return float(iv)
    return float("-inf")


async def _run_get_option_chain(args: GetOptionChainArgs) -> ToolResult:
    chain = await alpaca_options.get_option_chain(
        args.underlying, expiration_date=args.expiration_date
    )
    contracts = list(chain.values())
    contracts.sort(key=_contract_sort_key, reverse=True)
    top = contracts[:25]
    return ToolResult(
        content={
            "underlying": args.underlying,
            "expiration_date": args.expiration_date,
            "total": len(chain),
            "returned": len(top),
            "sort_key": "open_interest_or_iv",
            "contracts": top,
        }
    )


async def _run_get_crypto_bars(args: GetCryptoBarsArgs) -> ToolResult:
    df = await alpaca_crypto.get_crypto_bars(
        args.symbol, timeframe=args.timeframe, lookback=args.lookback
    )
    bars = _bars_payload(df, args.symbol)
    summary = {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "lookback": args.lookback,
        "count": len(bars),
        "first": bars[0] if bars else None,
        "last": bars[-1] if bars else None,
    }
    side = [
        SideEffect(
            type="chart",
            data={
                "kind": "candle",
                "title": f"{args.symbol} {args.timeframe} ({args.lookback})",
                "symbol": args.symbol,
                "bars": bars,
            },
        )
    ]
    return ToolResult(content=summary, side_effects=side)


async def _run_get_crypto_quote(args: GetCryptoQuoteArgs) -> ToolResult:
    q = await alpaca_crypto.get_crypto_latest_quote(args.symbol)
    return ToolResult(content=q)


async def _run_make_report(args: MakeReportArgs) -> ToolResult:
    # Defer to reports/store.py to materialize. Imported lazily to break import cycles.
    from app.services.reports import store

    record = await store.save_report(
        title=args.title,
        format=args.format,
        sections=[s.model_dump() for s in args.sections],
    )
    return ToolResult(
        content={"id": record["id"], "format": record["format"], "url": record["url"]},
        side_effects=[SideEffect(type="artifact", data=record)],
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class _ToolImpl:
    name: str
    description: str
    args_schema: type[BaseModel]
    run: Callable[[BaseModel], Awaitable[ToolResult]]


TOOLS: dict[str, _ToolImpl] = {
    "get_bars": _ToolImpl(
        name="get_bars",
        description="Fetch OHLCV bars for a symbol. Returns a summary + emits a candle chart side-effect.",
        args_schema=GetBarsArgs,
        run=_run_get_bars,
    ),
    "get_quote": _ToolImpl(
        name="get_quote",
        description="Latest bid/ask quote for a symbol.",
        args_schema=GetQuoteArgs,
        run=_run_get_quote,
    ),
    "get_snapshot": _ToolImpl(
        name="get_snapshot",
        description="Snapshot: latest trade/quote, today's bar, previous daily bar.",
        args_schema=GetSnapshotArgs,
        run=_run_get_snapshot,
    ),
    "compute_indicators": _ToolImpl(
        name="compute_indicators",
        description="Compute technical indicators on a symbol's bars. Emits an indicator-overlay chart.",
        args_schema=ComputeIndicatorsArgs,
        run=_run_compute_indicators,
    ),
    "compute_stats": _ToolImpl(
        name="compute_stats",
        description="Compute performance statistics (Sharpe/Sortino/drawdown/beta) for a symbol.",
        args_schema=ComputeStatsArgs,
        run=_run_compute_stats,
    ),
    "get_news": _ToolImpl(
        name="get_news",
        description="Recent news for a symbol from Alpaca's news feed.",
        args_schema=GetNewsArgs,
        run=_run_get_news,
    ),
    "screen": _ToolImpl(
        name="screen",
        description="Run a simple screen (momentum, mean_reversion, breakout, overbought, oversold) over a universe.",
        args_schema=ScreenArgs,
        run=_run_screen,
    ),
    "make_chart": _ToolImpl(
        name="make_chart",
        description="Render a custom chart from a ChartSpec. Use this to add charts beyond the ones data tools already emit.",
        args_schema=MakeChartArgs,
        run=_run_make_chart,
    ),
    "render_markdown": _ToolImpl(
        name="render_markdown",
        description="Emit a final markdown summary. Call this once at the end of your analysis.",
        args_schema=RenderMarkdownArgs,
        run=_run_render_markdown,
    ),
    "make_report": _ToolImpl(
        name="make_report",
        description="Generate a downloadable report artifact (html/pdf/xlsx/pptx/md). Use when the user asks for a report or one-pager.",
        args_schema=MakeReportArgs,
        run=_run_make_report,
    ),
    "get_option_chain": _ToolImpl(
        name="get_option_chain",
        description=(
            "Fetch the option chain for an underlying ticker. Returns up to 25 contracts "
            "ranked by open_interest (or implied_volatility when open_interest is unavailable). "
            "Optionally filter by expiration_date (YYYY-MM-DD)."
        ),
        args_schema=GetOptionChainArgs,
        run=_run_get_option_chain,
    ),
    "get_crypto_bars": _ToolImpl(
        name="get_crypto_bars",
        description="Fetch OHLCV bars for a crypto pair (e.g. 'BTC/USD'). Emits a candle chart side-effect.",
        args_schema=GetCryptoBarsArgs,
        run=_run_get_crypto_bars,
    ),
    "get_crypto_quote": _ToolImpl(
        name="get_crypto_quote",
        description="Latest bid/ask quote for a crypto pair (e.g. 'BTC/USD').",
        args_schema=GetCryptoQuoteArgs,
        run=_run_get_crypto_quote,
    ),
}


def to_grok_tool_specs() -> list[dict]:
    """Convert TOOLS into the JSON schema list the chat-completions API expects."""
    specs = []
    for t in TOOLS.values():
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.args_schema.model_json_schema(),
                },
            }
        )
    return specs
