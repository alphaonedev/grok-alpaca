# Prompt 07 — FastAPI v1 routes (including SSE chat)

## Goal
Stitch services into HTTP endpoints. The chat endpoint streams orchestrator events via Server-Sent Events.

## Tasks
1. `backend/app/api/v1/chat.py`
   - `POST /api/v1/chat` request body: `{conversation_id: str, message: str}`.
   - Response: `text/event-stream` from `sse-starlette.EventSourceResponse`.
   - Events are JSON-serialized `OrchestratorEvent`s emitted by `Orchestrator.run()`.
   - `POST /api/v1/chat/{conversation_id}/reset` clears history.

2. `backend/app/api/v1/market.py`
   - Routes from Prompt 02.

3. `backend/app/api/v1/analysis.py`
   - `POST /api/v1/analysis/indicators` body `{symbol, timeframe, lookback, indicators[], params}`.
   - `POST /api/v1/analysis/stats` body `{symbol, lookback, benchmark}`.
   - `POST /api/v1/analysis/screen` body `{strategy, universe, lookback}`.
   - `POST /api/v1/analysis/backtest` body `{symbol, lookback, signal_rule}`.

4. `backend/app/api/v1/reports.py`
   - `POST /api/v1/reports` body `{format, title, sections}` → returns `{id, url}`.
   - `GET /api/v1/reports/{id}` serves the file (HTML inline, others as downloads).
   - `GET /api/v1/reports` lists generated artifacts (id, title, format, created_at).

5. `backend/app/api/v1/stream_ws.py`
   - From Prompt 03.

6. `backend/app/main.py` — `include_router(...)` for each module under `/api/v1`. Set `openapi_url="/api/openapi.json"`.

7. Tests
   - `backend/tests/integration/test_chat_sse.py` — uses `httpx.AsyncClient` against the app; orchestrator is monkeypatched to emit a fixed event sequence; asserts the SSE byte stream matches.

## Acceptance
- `http://127.0.0.1:8000/docs` shows all routes.
- `npx openapi-typescript http://127.0.0.1:8000/api/openapi.json -o frontend/src/api/types.ts` generates clean types.
- `curl -N -X POST http://127.0.0.1:8000/api/v1/chat -H 'content-type: application/json' -d '{"conversation_id":"t","message":"hi"}'` streams events.
