# Architecture

## High-level

Two processes:

1. **Backend** — FastAPI on `127.0.0.1:8000`. Exposes REST + SSE + WebSocket.
2. **Frontend** — Vite/React on `127.0.0.1:5173`, proxying `/api` and `/ws` to the backend.

No reverse proxy. No database. State is:
- in-memory conversation history (per-orchestrator)
- on-disk JSON: watchlists at `~/.grok-alpaca/watchlist.json`, reports at `~/.grok-alpaca/reports/`
- browser `localStorage` for the chat panel

## Backend modules

```
backend/app/
├── main.py                      FastAPI factory, lifespan, mounts, /healthz
├── core/
│   ├── config.py                Settings (pydantic-settings)
│   ├── logging.py               structlog (console + json)
│   └── localhost_guard.py       refuses non-loopback bind
├── api/v1/
│   ├── chat.py                  POST /api/v1/chat (SSE)
│   ├── market.py                bars / quote / trade / snapshot / clock / news
│   ├── analysis.py              indicators / stats / screen / backtest
│   ├── reports.py               create / list / fetch artifacts
│   ├── watchlist.py             CRUD persisted JSON
│   └── stream_ws.py             WebSocket bridge to Alpaca live data
└── services/
    ├── alpaca/
    │   ├── historical.py        StockHistoricalDataClient wrappers
    │   ├── streaming.py         Single upstream stream + per-client fan-out
    │   ├── news.py
    │   └── market_clock.py
    ├── grok/
    │   ├── client.py            httpx → api.x.ai/v1 chat completions
    │   ├── prompts.py           ANALYST_SYSTEM_PROMPT
    │   ├── tools.py             10+ tool definitions + JSON-schema registry
    │   └── orchestrator.py      tool-call loop, streams events to API layer
    ├── analysis/
    │   ├── indicators.py        SMA EMA RSI MACD BBANDS ATR VWAP OBV STOCH
    │   ├── stats.py             returns sharpe sortino drawdown calmar beta
    │   ├── screeners.py         momentum mean_reversion breakout
    │   └── backtest.py          vectorized long-only signal backtester
    ├── reports/
    │   ├── store.py             on-disk artifact registry
    │   ├── markdown.py
    │   ├── html_artifact.py     self-contained HTML w/ Plotly CDN
    │   ├── xlsx_export.py       openpyxl
    │   ├── pdf_export.py        weasyprint(HTML → PDF)
    │   └── pptx_export.py       python-pptx
    └── watchlist.py             JSON file persistence
```

## The orchestrator loop

```
client                FastAPI               Orchestrator         Grok        Tools
  │                     │                       │                 │            │
  │── POST /chat ──────►│── run(conv,msg) ─────►│                 │            │
  │◄── SSE: token …─────│◄────── stream chunks ─│◄── chat_stream ─│            │
  │◄── SSE: tool_call ──│◄──                    │── tool_calls ──►│            │
  │                     │                       │── asyncio.gather ────────►│  │
  │                     │                       │◄── ToolResult + side_eff ─│  │
  │◄── SSE: chart ──────│                       │                            │  │
  │◄── SSE: artifact ───│                       │                            │  │
  │◄── SSE: tool_result │                       │                            │  │
  │                     │                       │── chat_stream (round 2) ──►│
  │◄── SSE: token …─────│                       │                            │
  │◄── SSE: done ───────│                       │                            │
```

Up to `GROK_MAX_TOOL_ROUNDS` (default 8) iterations.

## Tool registry

Each tool exposes `(name, description, args_schema, run)`. `args_schema` is a Pydantic model; `run` is an async coroutine returning a `ToolResult`. A `ToolResult` bundles:
- `content` — JSON-serializable payload fed back to the model
- `side_effects` — UI events (chart, artifact, markdown) the orchestrator surfaces directly to the client

The tools registered today:

| name | purpose |
|---|---|
| `get_bars` | OHLCV bars + emits candle chart |
| `get_quote` | latest bid/ask |
| `get_snapshot` | latest trade/quote + today's bar + prev daily bar |
| `compute_indicators` | technical indicators + emits indicator-overlay chart |
| `compute_stats` | Sharpe / Sortino / drawdown / beta |
| `get_news` | Alpaca news for a symbol |
| `screen` | momentum / mean_reversion / breakout / overbought / oversold |
| `make_chart` | render a custom ChartSpec |
| `render_markdown` | emit final markdown summary |
| `make_report` | generate downloadable artifact (md/html/xlsx/pdf/pptx) |

## Chart specs

A `ChartSpec` is a discriminated union (`kind ∈ {candle, line, indicator_overlay, performance}`). The backend produces them; the frontend renders them via either TradingView Lightweight Charts (candles) or Plotly-React (everything else). Embedded HTML reports use Plotly via CDN so the file is self-contained.

## WebSocket multiplexer

One process-wide `AlpacaStreamManager` holds **one** upstream connection. Per-browser WebSocket clients each get an `asyncio.Queue(maxsize=1000)`. The manager reference-counts symbol subscriptions: subscribes upstream on first listener, unsubscribes when last drops. Reconnect uses 1s/2s/4s/8s/16s/30s with jitter; on reconnect the manager re-subscribes the union of all symbols.

## Localhost guarantee

`backend/app/core/localhost_guard.ensure_localhost(host)` runs in the FastAPI lifespan and raises if `host` is `0.0.0.0`, `::`, `*`, or any resolved IP that isn't loopback. CI fails on `from alpaca.trading` or `TradingClient` references. CORS allows only `127.0.0.1:5173` and `localhost:5173`.
