"""Async Grok client.

Implementation note: we call the xAI OpenAI-compatible REST endpoint
(`https://api.x.ai/v1`) via httpx so the wire format is well-known and
stable. The `xai-sdk` Python package can be substituted later without
changing the surface this module exposes — see prompts/04-grok-client.md.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Literal

import httpx
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("grok.client")

_BASE_URL = "https://api.x.ai/v1"


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class GrokClient:
    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        s = get_settings()
        self._api_key = api_key or s.xai_api_key.get_secret_value()
        self._model = model or s.grok_model
        self._temperature = s.grok_temperature

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[Message] | list[dict],
        *,
        tools: list[dict] | None = None,
        tool_choice: str | dict = "auto",
        temperature: float | None = None,
        response_format: dict | None = None,
        parallel_tool_calls: bool = True,
        timeout: float = 60.0,
    ) -> dict:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [m.model_dump(exclude_none=True) if isinstance(m, Message) else m for m in messages],
            "temperature": self._temperature if temperature is None else temperature,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice
            body["parallel_tool_calls"] = parallel_tool_calls
        if response_format:
            body["response_format"] = response_format

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{_BASE_URL}/chat/completions", headers=self._headers(), json=body)
            r.raise_for_status()
            return r.json()

    async def chat_stream(
        self,
        messages: list[Message] | list[dict],
        *,
        tools: list[dict] | None = None,
        tool_choice: str | dict = "auto",
        temperature: float | None = None,
        parallel_tool_calls: bool = True,
        timeout: float = 120.0,
    ) -> AsyncIterator[dict]:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [m.model_dump(exclude_none=True) if isinstance(m, Message) else m for m in messages],
            "temperature": self._temperature if temperature is None else temperature,
            "stream": True,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice
            body["parallel_tool_calls"] = parallel_tool_calls

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{_BASE_URL}/chat/completions", headers=self._headers(), json=body) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        return
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        log.warning("grok.stream.bad_json", line=data[:200])
