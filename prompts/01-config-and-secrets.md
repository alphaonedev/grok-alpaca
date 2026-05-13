# Prompt 01 — Config, logging, and the localhost guard

## Goal
Wire up application configuration, structured logging, and a startup guard that refuses to bind to anything other than the loopback interface.

## Tasks
1. `backend/app/core/config.py`
   - `Settings(BaseSettings)` via `pydantic-settings`. Loads from `.env` and process env.
   - Fields: `xai_api_key: SecretStr`, `alpaca_api_key: SecretStr`, `alpaca_secret_key: SecretStr`, `alpaca_data_feed: Literal["iex","sip"] = "iex"`, `host: str = "127.0.0.1"`, `port: int = 8000`, `log_level: str = "INFO"`, `log_format: Literal["console","json"] = "console"`, `grok_model: str = "grok-4-0709"`, `grok_temperature: float = 0.3`, `grok_max_tool_rounds: int = 8`, `data_dir: Path = Path("~/.grok-alpaca").expanduser()`.
   - `@lru_cache` `get_settings()` accessor.
   - `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.

2. `backend/app/core/logging.py`
   - `configure_logging(level, format)` using `structlog`. Console renderer for dev, JSON renderer for prod.
   - Bridge stdlib logging to structlog.

3. `backend/app/core/localhost_guard.py`
   - `ensure_localhost(host: str) -> None` — raises `RuntimeError` if host is `0.0.0.0`, `::`, or resolves to a non-loopback address. Permit `127.0.0.1`, `localhost`, `::1`.

4. `backend/app/main.py`
   - FastAPI app factory `create_app() -> FastAPI`.
   - Lifespan calls `configure_logging` and `ensure_localhost(settings.host)`. Lifespan should also `data_dir.mkdir(parents=True, exist_ok=True)`.
   - CORS middleware allowing only `http://127.0.0.1:5173` and `http://localhost:5173`.
   - `GET /healthz` returns `{"ok": True, "service": "grok-alpaca"}`.
   - Mount routers under `/api/v1` (stubbed — empty `APIRouter()`s are fine for now).
   - Module-level `app = create_app()` for `uvicorn app.main:app`.

5. Tests
   - `backend/tests/unit/test_localhost_guard.py` — asserts `0.0.0.0` raises and `127.0.0.1` passes.
   - `backend/tests/unit/test_config.py` — asserts env vars override defaults.

## Acceptance
- `uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1` boots.
- `curl http://127.0.0.1:8000/healthz` returns `{"ok":true,...}`.
- `HOST=0.0.0.0 uv run uvicorn app.main:app --app-dir backend --host 0.0.0.0` fails fast with a clear error.
- `uv run pytest backend/tests/unit/test_localhost_guard.py backend/tests/unit/test_config.py` green.
