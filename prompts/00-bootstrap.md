# Prompt 00 — Bootstrap

## Role
You are setting up the `grok-alpaca` project from scratch. The repo already contains this prompt and nothing else (or perhaps a partial scaffold from earlier — if so, reconcile, don't duplicate).

## Goal
Create a clean Python + Node project skeleton that boots.

## Tasks
1. Initialize uv project. Create `pyproject.toml` (Python ≥3.11) with dependencies:
   - Runtime: `fastapi uvicorn[standard] xai-sdk alpaca-py pandas pandas-ta numpy pydantic pydantic-settings structlog rich httpx websockets markdown-it-py[plugins] jinja2 openpyxl python-pptx weasyprint sse-starlette orjson python-dotenv`
   - Dev: `pytest pytest-asyncio pytest-cov respx ruff black mypy`
2. Create `.gitignore` covering Python, Node, .env, .venv, .DS_Store, build artifacts, and user data dir.
3. Create `LICENSE` (MIT, current year).
4. Create `.env.example` with keys: `XAI_API_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_DATA_FEED=iex`, `HOST=127.0.0.1`, `PORT=8000`, `LOG_LEVEL=INFO`, `LOG_FORMAT=console`, `GROK_MODEL=grok-4-0709`, `GROK_TEMPERATURE=0.3`, `GROK_MAX_TOOL_ROUNDS=8`, `DATA_DIR=~/.grok-alpaca`.
5. Create `Makefile` with targets: `install`, `dev`, `backend`, `frontend`, `openapi`, `gen-types`, `test`, `lint`, `fmt`, `clean`. The `lint` target must include a grep that fails the build if `from alpaca.trading` or `TradingClient` appears anywhere in `backend/app/`.
6. Create `scripts/run-dev.sh` that runs uvicorn (`--app-dir backend`) + `npm run dev` concurrently, with a trap to clean up.
7. Create directory skeleton: `backend/app/{core,api/v1,services/{grok,alpaca,analysis,reports}}`, `backend/tests/{unit,integration}`, `frontend/`, `docs/`, `prompts/`, `scripts/`, `.github/workflows/`.
8. Run `uv sync` to verify the pyproject parses.

## Constraints
- This is a **read-only** market-data project. No `TradingClient`. No `alpaca.trading.*` imports anywhere.
- Localhost-only. Anywhere a host is referenced, default to `127.0.0.1`.

## Acceptance
- `uv sync` exits 0.
- `make lint` runs (may fail on missing files, that's fine — the grep guard must not error).
- `git status` shows no `.env` or `.venv` ever.
