# Prompt 04 — Grok client

## Goal
Typed async wrapper around the official `xai-sdk` Python library exposing chat, streaming, and tool calling.

## Reference
- xAI SDK: https://github.com/xai-org/xai-sdk-python
- Docs: https://docs.x.ai/

## Tasks
1. `backend/app/services/grok/client.py`
   - `class GrokClient`:
     - Built from `Settings`. Holds `xai_sdk.AsyncClient(api_key=...)`.
     - `async def chat(messages, *, tools=None, tool_choice="auto", temperature=None, response_format=None) -> ChatResponse`
     - `async def chat_stream(messages, *, tools=None, ...) -> AsyncIterator[ChatStreamEvent]` — yields a normalized event stream: `{"type":"token","text":...}`, `{"type":"tool_call","id":...,"name":...,"arguments":{...}}`, `{"type":"finish","reason":...}`.
     - Default model from `settings.grok_model` (`grok-4-0709`). Default temperature from settings.
     - Pass `parallel_tool_calls=True`.
   - Pydantic models: `Message(role: Literal["system","user","assistant","tool"], content: str | list[ContentPart], tool_calls: list[ToolCall] | None, tool_call_id: str | None)`.

2. `backend/app/services/grok/prompts.py`
   - `ANALYST_SYSTEM_PROMPT` — opinionated system prompt. The analyst persona must:
     - Always cite symbol, timeframe, last-trade timestamp.
     - Use `get_bars` / `compute_indicators` before drawing conclusions.
     - Prefer `make_chart` over text descriptions of price action.
     - End with a markdown summary via `render_markdown`.
     - Decline to give buy/sell recommendations; instead present evidence + scenarios.
     - Never claim to place trades; this tool has no trading capability.

3. Tests
   - `backend/tests/unit/test_grok_client.py` — monkeypatch the underlying xai-sdk client; assert message construction, tool-call normalization, streaming event shape.
   - `backend/tests/integration/test_grok_live.py` — marked `@pytest.mark.integration`, only runs if `XAI_API_KEY` env var is set; sends "say hello" and asserts non-empty response.

## Acceptance
- `uv run pytest backend/tests/unit/test_grok_client.py` green.
- With a real key: `uv run pytest -m integration backend/tests/integration/test_grok_live.py` returns a real Grok response.
