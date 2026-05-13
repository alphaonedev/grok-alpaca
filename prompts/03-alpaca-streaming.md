# Prompt 03 — Alpaca live streaming

## Goal
A single asyncio-based manager that maintains one upstream connection to Alpaca's `StockDataStream` and fans incoming quotes/trades/bars out to many connected browser WebSocket clients.

## Tasks
1. `backend/app/services/alpaca/streaming.py`
   - Class `AlpacaStreamManager`:
     - Holds one `StockDataStream(api_key, secret_key, feed=ALPACA_DATA_FEED)` instance.
     - Maintains: `subscribers: dict[str, set[asyncio.Queue]]` keyed by symbol; reference-counted subscriptions.
     - `async def start()` — runs the stream in a background task. Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, capped at 30s) and jitter.
     - `async def subscribe(symbols, queue, kinds=("quotes","trades","bars"))` — adds queue to per-symbol set, calls `stream.subscribe_*` for new symbols only.
     - `async def unsubscribe(queue)` — drop queue, drop upstream subs if no remaining listeners.
     - Each upstream event is JSON-serialized into a small envelope `{"kind":"quote","symbol":"AAPL","data":{...},"ts":...}` and put on every matching queue.
   - Singleton accessor `get_stream_manager()`.

2. `backend/app/api/v1/stream_ws.py`
   - `@router.websocket("/ws")`:
     - Accept the connection. Create a per-client `asyncio.Queue(maxsize=1000)`.
     - Receive client control frames: `{"action":"subscribe","symbols":["AAPL","MSFT"],"kinds":["quotes","trades"]}`, `{"action":"unsubscribe","symbols":[...]}`, `{"action":"ping"}`.
     - Background task pulls from queue and sends to client; if queue fills up (slow consumer), drop oldest.

3. `backend/app/main.py`
   - Lifespan starts the singleton stream manager and stops it cleanly.

4. Tests
   - `backend/tests/unit/test_streaming.py` — fakes the upstream stream by injecting events into the manager's internal dispatch and asserting fan-out.

## Constraints
- Only one upstream Alpaca connection regardless of browser count.
- Backpressure: bound queues, drop on overflow with a `dropped_messages` counter logged every 10s.
- No live trading APIs.

## Acceptance
- `wscat -c ws://127.0.0.1:8000/api/v1/stream/ws` and `{"action":"subscribe","symbols":["AAPL"],"kinds":["quotes","trades"]}` streams real ticks during market hours.
- Killing and restarting the upstream stream (simulated) results in client receiving a `{"kind":"system","data":{"reconnected":true}}` notice with no client-side reconnect required.
