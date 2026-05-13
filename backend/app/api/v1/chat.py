"""Chat endpoint — SSE stream over Orchestrator events."""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.services.grok.orchestrator import Orchestrator, reset_conversation

router = APIRouter()
_orchestrator: Orchestrator | None = None


def _get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


class ChatBody(BaseModel):
    conversation_id: str
    message: str


@router.post("")
async def chat(body: ChatBody) -> EventSourceResponse:
    orch = _get_orchestrator()

    async def gen() -> AsyncIterator[dict]:
        try:
            async for event in orch.run(body.conversation_id, body.message):
                yield {"data": json.dumps(event)}
        except Exception as exc:  # noqa: BLE001
            yield {"data": json.dumps({"type": "error", "error": str(exc)})}

    return EventSourceResponse(gen())


@router.post("/{conversation_id}/reset")
async def reset(conversation_id: str) -> dict:
    reset_conversation(conversation_id)
    return {"ok": True}
