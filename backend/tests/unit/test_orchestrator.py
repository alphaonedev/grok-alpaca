"""Orchestrator unit test with a faked GrokClient."""

import json

import pytest

from app.services.grok import orchestrator as orch_mod
from app.services.grok.orchestrator import Orchestrator


class FakeClient:
    """Yields scripted SSE-like chunks."""

    def __init__(self, scripts):
        self.scripts = scripts
        self.call = 0

    async def chat_stream(self, messages, *, tools=None, tool_choice="auto", **_):
        script = self.scripts[self.call]
        self.call += 1
        for chunk in script:
            yield chunk


def _delta(text=None, tool_calls=None, finish_reason=None):
    delta = {}
    if text is not None:
        delta["content"] = text
    if tool_calls is not None:
        delta["tool_calls"] = tool_calls
    return {"choices": [{"delta": delta, "finish_reason": finish_reason}]}


@pytest.mark.asyncio
async def test_orchestrator_two_round_tool_call():
    # Round 1: emit a tool call for `render_markdown` (cheapest tool, no Alpaca).
    round1 = [
        _delta(
            tool_calls=[
                {
                    "index": 0,
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "render_markdown", "arguments": json.dumps({"markdown": "# hi"})},
                }
            ]
        ),
        _delta(finish_reason="tool_calls"),
    ]
    # Round 2: emit final text and stop.
    round2 = [_delta(text="Done."), _delta(finish_reason="stop")]

    orch_mod._CONVERSATIONS.clear()
    orch = Orchestrator(client=FakeClient([round1, round2]))  # type: ignore[arg-type]

    events = []
    async for e in orch.run("conv-test", "do it"):
        events.append(e)

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "markdown" in types or "tool_result" in types
    assert types[-1] == "done"
