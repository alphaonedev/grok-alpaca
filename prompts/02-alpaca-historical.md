# Prompt 02 — Alpaca historical service

## Goal
A small, typed service that wraps `alpaca-py` historical clients for stocks (and a thin pass-through for crypto/options/news). **Never imports `alpaca.trading`.**

## Tasks
1. `backend/app/services/alpaca/historical.py`
   - Lazy-built `StockHistoricalDataClient` using settings.
   - Functions (async-capable; alpaca-py is sync but wrap with `asyncio.to_thread`):
     - `get_bars(symbol: str | list[str], timeframe: str, lookback: str | None, start: datetime | None, end: datetime | None) -> pd.DataFrame`
       - `timeframe` strings: `"1Min"`, `"5Min"`, `"15Min"`, `"1Hour"`, `"1Day"`, `"1Week"`. Convert to `alpaca.data.timeframe.TimeFrame`.
       - `lookback` strings: `"30d"`, `"6mo"`, `"1y"`, `"5y"`. Resolve to start/end.
     - `get_latest_quote(symbol: str) -> dict`
     - `get_latest_trade(symbol: str) -> dict`
     - `get_snapshot(symbol: str | list[str]) -> dict` — wraps `get_stock_snapshot`.
   - Return shape: DataFrames are JSON-serializable via `df.reset_index().to_dict(orient="records")`. Quotes/trades return plain dicts.

2. `backend/app/services/alpaca/options.py`
   - Wrap `OptionHistoricalDataClient.get_option_chain` and `get_option_bars`.

3. `backend/app/services/alpaca/crypto.py`
   - Wrap `CryptoHistoricalDataClient` similarly to stocks.

4. `backend/app/services/alpaca/news.py`
   - `NewsClient.get_news(symbols, start, end, limit)`.

5. `backend/app/services/alpaca/market_clock.py`
   - GET `https://data.alpaca.markets/v2/clock` and `/v2/calendar` via httpx (or use `alpaca-py` if available). Returns `is_open`, `next_open`, `next_close`.

6. `backend/app/api/v1/market.py`
   - `GET /api/v1/market/bars?symbol=AAPL&timeframe=1Day&lookback=30d`
   - `GET /api/v1/market/quote/{symbol}`
   - `GET /api/v1/market/trade/{symbol}`
   - `GET /api/v1/market/snapshot/{symbol}`
   - `GET /api/v1/market/clock`
   - `GET /api/v1/market/news?symbol=AAPL&limit=20`
   - All endpoints typed with pydantic response models so the OpenAPI schema is precise.

7. Tests
   - `backend/tests/unit/test_alpaca_historical.py` with `respx` mocking the underlying HTTP calls (alpaca-py uses httpx under the hood; mock at the URL level: `https://data.alpaca.markets/v2/stocks/AAPL/bars`).

## Constraints
- Read-only. **Do not** import `alpaca.trading`.
- All clients accept Alpaca keys via the constructed `Settings`.

## Acceptance
- `uv run pytest backend/tests/unit/test_alpaca_historical.py` green with respx mocks.
- `curl 'http://127.0.0.1:8000/api/v1/market/bars?symbol=AAPL&timeframe=1Day&lookback=5d'` returns JSON during market hours.
