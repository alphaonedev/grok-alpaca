"""Orchestrator — runs the Grok tool-call loop and streams events to the UI."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from typing import Any, AsyncIterator

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.grok.client import GrokClient, Message
from app.services.grok.prompts import ANALYST_SYSTEM_PROMPT
from app.services.grok.tools import TOOLS, to_grok_tool_specs

log = get_logger("grok.orchestrator")

_CONVERSATIONS: dict[str, list[Message]] = defaultdict(list)


def _seed(conv_id: str) -> list[Message]:
    if conv_id not in _CONVERSATIONS:
        _CONVERSATIONS[conv_id] = [Message(role="system", content=ANALYST_SYSTEM_PROMPT)]
    return _CONVERSATIONS[conv_id]


def reset_conversation(conv_id: str) -> None:
    _CONVERSATIONS.pop(conv_id, None)


class Orchestrator:
    def __init__(self, client: GrokClient | None = None) -> None:
        self.client = client or GrokClient()
        self.tool_specs = to_grok_tool_specs()

    async def run(self, conversation_id: str, user_message: str) -> AsyncIterator[dict[str, Any]]:
        settings = get_settings()
        messages = _seed(conversation_id)
        messages.append(Message(role="user", content=user_message))

        for round_idx in range(settings.grok_max_tool_rounds):
            log.info("orchestrator.round", round=round_idx, conv=conversation_id)
            assembled = _AssembledMessage()
            try:
                async for chunk in self.client.chat_stream(
                    messages=[m.model_dump(exclude_none=True) for m in messages],
                    tools=self.tool_specs,
                ):
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    if "content" in delta and delta["content"]:
                        assembled.content += delta["content"]
                        yield {"type": "token", "text": delta["content"]}
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc in delta["tool_calls"]:
                            assembled.absorb_tool_call_delta(tc)
                    if choices[0].get("finish_reason"):
                        assembled.finish_reason = choices[0]["finish_reason"]
            except Exception as exc:  # noqa: BLE001
                log.exception("orchestrator.stream_failed", error=str(exc))
                yield {"type": "error", "error": str(exc)}
                return

            tool_calls = list(assembled.tool_calls())
            assistant_msg = Message(
                role="assistant",
                content=assembled.content or None,
                tool_calls=tool_calls if tool_calls else None,
            )
            messages.append(assistant_msg)

            if not tool_calls:
                yield {"type": "done", "finish_reason": assembled.finish_reason}
                return

            # Execute tool calls in parallel.
            tasks = [self._execute_tool_call(tc) for tc in tool_calls]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            for tc, (tool_msg, side_effects, summary) in zip(tool_calls, results):
                yield {
                    "type": "tool_call",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": _safe_parse_json(tc["function"].get("arguments", "{}")),
                }
                for eff in side_effects:
                    yield {"type": eff.type, "data": eff.data}
                yield {
                    "type": "tool_result",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "summary": summary,
                }
                messages.append(tool_msg)

        yield {"type": "done", "finish_reason": "max_rounds"}

    async def _execute_tool_call(self, tc: dict):
        name = tc["function"]["name"]
        args_raw = tc["function"].get("arguments") or "{}"
        side_effects = []
        try:
            tool = TOOLS[name]
            args_dict = _safe_parse_json(args_raw)
            args = tool.args_schema.model_validate(args_dict)
            result = await tool.run(args)
            content_str = json.dumps(_jsonable(result.content))
            side_effects = result.side_effects
            summary = _summarize(result.content)
        except KeyError:
            content_str = json.dumps({"error": f"unknown tool {name!r}"})
            summary = {"error": f"unknown tool {name!r}"}
        except Exception as exc:  # noqa: BLE001
            log.exception("tool.failed", name=name, error=str(exc))
            content_str = json.dumps({"error": str(exc)})
            summary = {"error": str(exc)}
        tool_msg = Message(role="tool", tool_call_id=tc["id"], name=name, content=content_str)
        return tool_msg, side_effects, summary


class _AssembledMessage:
    """Streaming chunks include partial tool-call argument strings — assemble them."""

    def __init__(self) -> None:
        self.content: str = ""
        self._tool_calls: dict[int, dict] = {}
        self.finish_reason: str | None = None

    def absorb_tool_call_delta(self, delta: dict) -> None:
        idx = delta.get("index", 0)
        cur = self._tool_calls.setdefault(
            idx,
            {"id": delta.get("id") or f"call_{uuid.uuid4().hex[:8]}", "type": "function", "function": {"name": "", "arguments": ""}},
        )
        if "id" in delta:
            cur["id"] = delta["id"]
        fn = delta.get("function") or {}
        if "name" in fn:
            cur["function"]["name"] += fn["name"]
        if "arguments" in fn:
            cur["function"]["arguments"] += fn["arguments"]

    def tool_calls(self) -> list[dict]:
        return [self._tool_calls[k] for k in sorted(self._tool_calls)]


def _safe_parse_json(s: str | dict) -> dict:
    if isinstance(s, dict):
        return s
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return {}


def _summarize(content: Any) -> Any:
    if isinstance(content, dict):
        return {k: (v if not isinstance(v, list) or len(v) <= 5 else f"<{len(v)} items>") for k, v in content.items()}
    if isinstance(content, list):
        return f"<{len(content)} items>"
    return content


def _jsonable(x: Any) -> Any:
    import pandas as pd

    if isinstance(x, pd.DataFrame):
        return x.reset_index().to_dict(orient="records")
    if isinstance(x, pd.Series):
        return x.to_dict()
    return x
