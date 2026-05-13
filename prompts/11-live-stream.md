# Prompt 11 — Live stream wiring (browser-side WebSocket)

## Goal
Make the UI feel alive: watchlist ticks, chart's last candle grows from live trades.

## Tasks
1. `src/hooks/useWebSocket.ts`
   - Connects to `/ws` (proxied to backend `/api/v1/stream/ws`).
   - Auto-reconnect with exponential backoff + jitter.
   - Exposes `subscribe(symbols, kinds)`, `unsubscribe(symbols)`, and an event subject (`onEvent: (evt) => void`).
   - One singleton connection per app.

2. `src/components/watchlist/WatchList.tsx`
   - For each row, subscribe to quotes for that symbol.
   - Show last, bid, ask, %chg vs prev close.
   - Flash row background green/red on tick.

3. `src/components/chart/CandleChart.tsx` (extend)
   - When active symbol has live trades streaming, mutate the last bar's `close/high/low/volume` on each tick. When the bar period rolls over, push a new bar.

4. `src/components/snapshot/SnapshotPanel.tsx`
   - Refetches `/api/v1/market/snapshot/{symbol}` every 10s; combines with live tick for "as of" timestamp.

5. Tests
   - Manual: open dev tools network panel — confirm one WS connection regardless of how many components subscribe.
   - Playwright e2e: app loads → after market open, watchlist row updates within 5s (or, in CI, against a fake-stream fixture).

## Acceptance
- Single WS connection in DevTools.
- Live ticks visible during market hours.
- Last candle grows tick by tick on the active symbol.
