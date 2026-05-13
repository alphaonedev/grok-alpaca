"""FastAPI application factory + entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.localhost_guard import ensure_localhost
from app.core.logging import configure_logging, get_logger

log = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level, format=settings.log_format)
    ensure_localhost(settings.host)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "reports").mkdir(parents=True, exist_ok=True)

    log.info(
        "startup",
        host=settings.host,
        port=settings.port,
        grok_model=settings.grok_model,
        data_feed=settings.alpaca_data_feed,
        data_dir=str(settings.data_dir),
    )

    # Start streaming manager lazily on first WS connect; nothing to do here yet.
    try:
        yield
    finally:
        log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="grok-alpaca",
        description="Localhost financial analysis: xAI Grok + Alpaca real-time data.",
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict:
        return {"ok": True, "service": "grok-alpaca", "version": "0.1.0"}

    # Router registration — modules are imported lazily so partial scaffolds boot.
    _mount_routers(app)

    return app


def _mount_routers(app: FastAPI) -> None:
    from app.api.v1 import market, analysis, chat, reports, stream_ws, watchlist

    app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(watchlist.router, prefix="/api/v1/watchlists", tags=["watchlists"])
    app.include_router(stream_ws.router, prefix="/api/v1/stream", tags=["stream"])


app = create_app()
