# Prompt 12 — Watchlist + snapshot

## Goal
Persistent watchlist managed via the web UI, with a rich snapshot panel.

## Tasks
1. Backend: `backend/app/services/watchlist.py`
   - JSON file at `~/.grok-alpaca/watchlist.json`. Schema: `{name: str, symbols: list[str]}[]`.
   - Default watchlist (created on first run): `{name: "Default", symbols: ["SPY","QQQ","AAPL","MSFT","NVDA","AMD","META","GOOGL","AMZN","TSLA"]}`.
   - Async functions: `list_watchlists`, `get_watchlist(name)`, `add_symbol(name, symbol)`, `remove_symbol(name, symbol)`, `create_watchlist`, `delete_watchlist`.

2. Backend: `backend/app/api/v1/watchlist.py`
   - `GET /api/v1/watchlists`
   - `POST /api/v1/watchlists` body `{name, symbols}`
   - `DELETE /api/v1/watchlists/{name}`
   - `POST /api/v1/watchlists/{name}/symbols` body `{symbol}`
   - `DELETE /api/v1/watchlists/{name}/symbols/{symbol}`

3. `scripts/seed-watchlist.py` — creates default file if missing.

4. Frontend: `src/components/watchlist/WatchList.tsx`
   - List rows with live ticks (from Prompt 11) and `+`/`x` controls.
   - Switcher for multiple lists.
   - Add-symbol input with debounced `/api/v1/market/snapshot/{symbol}` lookahead to validate.

5. Frontend: `src/components/snapshot/SnapshotPanel.tsx`
   - Right side of the chart pane (or below it). Fields: last, prev close, day change/%, day range, 52w hi/lo, volume, avg volume, market cap (if available).

## Acceptance
- Add/remove symbols persists across server restart.
- Default watchlist materializes on first run.
- Snapshot updates every 10s.
