"""WebSocket stream — fans Alpaca live data to many browser clients."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.alpaca.streaming import get_stream_manager

log = get_logger("ws")

router = APIRouter()


@router.websocket("/ws")
async def stream(ws: WebSocket) -> None:
    await ws.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    mgr = get_stream_manager()
    await mgr.start()
    sub = None

    async def sender():
        while True:
            evt = await queue.get()
            await ws.send_text(json.dumps(evt))

    sender_task = asyncio.create_task(sender())
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"kind": "error", "data": {"reason": "bad json"}}))
                continue

            action = msg.get("action")
            if action == "subscribe":
                symbols = [s.upper() for s in msg.get("symbols", [])]
                kinds = tuple(msg.get("kinds", ["quotes", "trades"]))
                sub = await mgr.subscribe(symbols, queue, kinds=kinds)
                await ws.send_text(json.dumps({"kind": "system", "data": {"subscribed": symbols, "kinds": kinds}}))
            elif action == "unsubscribe" and sub is not None:
                await mgr.unsubscribe(sub)
                sub = None
                await ws.send_text(json.dumps({"kind": "system", "data": {"unsubscribed": True}}))
            elif action == "ping":
                await ws.send_text(json.dumps({"kind": "pong"}))
            else:
                await ws.send_text(json.dumps({"kind": "error", "data": {"reason": "unknown action"}}))
    except WebSocketDisconnect:
        pass
    finally:
        sender_task.cancel()
        if sub is not None:
            await mgr.unsubscribe(sub)
