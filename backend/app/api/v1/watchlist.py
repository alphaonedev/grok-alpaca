"""Watchlist endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import watchlist as wl

router = APIRouter()


class CreateWatchlistBody(BaseModel):
    name: str
    symbols: list[str]


class AddSymbolBody(BaseModel):
    symbol: str


@router.get("")
async def list_all() -> dict:
    return {"watchlists": await wl.list_watchlists()}


@router.post("")
async def create(body: CreateWatchlistBody) -> dict:
    try:
        return await wl.create_watchlist(body.name, body.symbols)
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.delete("/{name}")
async def delete(name: str) -> dict:
    await wl.delete_watchlist(name)
    return {"ok": True}


@router.post("/{name}/symbols")
async def add_symbol(name: str, body: AddSymbolBody) -> dict:
    try:
        return await wl.add_symbol(name, body.symbol.upper())
    except KeyError:
        raise HTTPException(404, f"watchlist {name!r} not found")


@router.delete("/{name}/symbols/{symbol}")
async def remove_symbol(name: str, symbol: str) -> dict:
    try:
        return await wl.remove_symbol(name, symbol.upper())
    except KeyError:
        raise HTTPException(404, f"watchlist {name!r} not found")
