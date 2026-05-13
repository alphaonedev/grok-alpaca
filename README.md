# grok-alpaca

**Localhost financial analysis: xAI Grok + Alpaca real-time market data, with a React web UI.**

A read-only research workbench that fuses **xAI Grok** (analyst brain, tool-using LLM) with **Alpaca Markets** (real-time + historical data) and exposes both through a polished React UI. Ask Grok questions in natural language; it pulls live bars, computes indicators, generates charts, and writes markdown / HTML / PDF / XLSX / PPTX reports.

> **Read-only by design.** No trading client is imported. CI fails if `alpaca.trading` or `TradingClient` appears anywhere in the codebase.

```
┌──────────────────────────────────────────────────────────────────────┐
│  React (Vite) :5173  ◄── proxy ──►  FastAPI :8000                    │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐    ┌──────────────────┐  │
│  │ Watchlist│ │ Chart Canvas │ │ Chat ▍   │◄──►│  Orchestrator    │  │
│  │ live tick│ │ candles + ind│ │ streaming│    │  └─ xAI Grok     │  │
│  └────▲─────┘ └──────────────┘ └──────────┘    │  └─ Tools (15+)  │  │
│       │                                        │  └─ Alpaca data  │  │
│       └─ WebSocket multiplexer ◄───────────────┤  └─ Reports gen  │  │
│                                                └──────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                            127.0.0.1 only
```

## Features

- **Chat with Grok** — streaming responses with **inline tool-call traces** so you can see what data the model pulled.
- **Live market data** — Alpaca WebSocket multiplexed across the UI; one upstream connection, many browser tabs.
- **Charts** — TradingView Lightweight Charts for OHLC, Plotly for indicators. Crosshair, zoom, candles updating tick-by-tick.
- **Indicators & stats** — SMA, EMA, RSI, MACD, Bollinger, ATR, VWAP, OBV, Stoch · Sharpe/Sortino/Calmar/drawdown/beta.
- **Screeners** — momentum, mean-reversion, breakout, overbought/oversold.
- **Backtester** — vectorized long-only signal backtester (SMA cross, RSI oversold).
- **Reports** — Grok can generate Markdown · HTML · XLSX · PDF · PPTX artifacts; rendered inline (HTML in sandboxed iframe) or downloadable.
- **Watchlists** — persisted across restart; live ticks on each row.
- **Localhost-guard** — refuses any non-loopback bind at startup.

## Quickstart (≈30 seconds)

```bash
git clone https://github.com/<you>/grok-alpaca && cd grok-alpaca
cp .env.example .env       # fill XAI_API_KEY, ALPACA_API_KEY, ALPACA_SECRET_KEY
make install               # uv sync + npm install
make dev                   # uvicorn :8000 + vite :5173
open http://127.0.0.1:5173
```

Get keys at:
- xAI: https://console.x.ai/
- Alpaca: https://app.alpaca.markets/paper/dashboard/overview (paper account is plenty)

## Architecture

```mermaid
flowchart LR
  UI[React + Vite] -- /api -->|HTTP + SSE| API[FastAPI]
  UI -- /ws -->|WebSocket| API
  API -- chat --> ORCH[Orchestrator]
  ORCH -- tool calls --> GROK[xAI Grok]
  ORCH -- tool calls --> TOOLS[Tool registry]
  TOOLS --> AL[Alpaca historical]
  TOOLS --> AN[Indicators / stats / screeners]
  TOOLS --> RPT[Reports: md/html/xlsx/pdf/pptx]
  API <-- WS --> ALSTREAM[Alpaca live stream]
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module-by-module detail.

## NHI prompts — build this yourself, one feature at a time

The [`prompts/`](prompts/) directory contains **18 self-contained prompts** you can paste into Claude Code CLI to rebuild or extend every feature in this repo. Each one has clear acceptance criteria and references only file paths — no chat-history dependencies.

```bash
cd grok-alpaca
claude                        # start Claude Code
# paste prompts/00-bootstrap.md → verify → commit
# paste prompts/01-config-and-secrets.md → verify → commit
# ...etc
```

See [`docs/PROMPTS.md`](docs/PROMPTS.md) for the index and tips on writing your own.

## Anthropic Skills

This repo uses Anthropic Skills at **build time** (Claude Code loads them when relevant) and mirrors their capabilities in **runtime Python** so Grok can call them as tools. See [`docs/SKILLS.md`](docs/SKILLS.md) for the mapping.

## Security posture

- Binds only to `127.0.0.1`. Boot fails if `HOST` resolves to anything non-loopback.
- No live-trading client imported. CI grep guard enforces this.
- API keys stay in `.env`; never logged, never echoed.
- CORS allows only `http://127.0.0.1:5173`.
- Grok-generated HTML artifacts render in **sandboxed iframes** (`sandbox="allow-scripts"`).

## Why not `grok-cli` under the hood?

[`alphaonedev/grok-cli`](https://github.com/alphaonedev/grok-cli) is a TypeScript/Bun **standalone CLI** with no embeddable Python API. Shelling out to it would add a Bun runtime dependency on every machine and force us to parse newline-delimited JSON events for an agent loop we'd duplicate anyway. We use the **xAI REST API** directly (OpenAI-compatible at `api.x.ai/v1`) — the official [`xai-sdk`](https://github.com/xai-org/xai-sdk-python) Python package can be swapped in without changing this project's surface.

## Repository layout

```
backend/         FastAPI + services (alpaca, grok, analysis, reports)
frontend/        Vite + React + TS + Tailwind
prompts/         18 NHI prompts for Claude Code CLI
docs/            Architecture, prompts, skills
scripts/         run-dev.sh, seed-watchlist.py
.github/         CI workflows
```

## Make targets

| target        | what it does |
|---------------|-------------|
| `make install`| `uv sync --all-extras` + `npm install` |
| `make dev`    | backend + frontend concurrently |
| `make test`   | pytest + vitest |
| `make lint`   | ruff + black + mypy + eslint + no-trading-imports guard |
| `make fmt`    | autoformat everything |
| `make gen-types` | regenerate `frontend/src/api/types.ts` from FastAPI's OpenAPI |

## License

[MIT](LICENSE).

## Disclaimer

This is a research tool, not investment advice. The Grok analyst persona is configured to **decline** buy/sell recommendations and instead present evidence and scenarios. Markets are risky; use your own judgment.
