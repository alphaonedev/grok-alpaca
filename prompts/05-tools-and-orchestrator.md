# Prompt 05 — Tools + orchestrator

## Goal
Define every tool Grok can call, and the loop that executes them and feeds results back.

## Tasks
1. `backend/app/services/grok/tools.py`
   - One Pydantic model per tool's arguments. Examples:
     - `GetBarsArgs(symbol: str, timeframe: Literal["1Min","5Min","15Min","1Hour","1Day","1Week"], lookback: str)` — e.g. `"90d"`.
     - `GetQuoteArgs(symbol: str)`
     - `GetSnapshotArgs(symbol: str)`
     - `ComputeIndicatorsArgs(symbol: str, timeframe: str, lookback: str, indicators: list[Literal["SMA","EMA","RSI","MACD","BBANDS","ATR","VWAP","OBV","STOCH"]], params: dict[str, Any] = {})`
     - `ComputeStatsArgs(symbol: str, lookback: str, benchmark: str = "SPY")`
     - `GetNewsArgs(symbol: str, limit: int = 20)`
     - `GetMarketMoversArgs()`
     - `GetMostActiveArgs()`
     - `ScreenArgs(strategy: Literal["momentum","mean_reversion","breakout"], universe: list[str] | None = None, lookback: str = "60d")`
     - `MakeChartArgs(chart_spec: ChartSpec)` — `ChartSpec` is a discriminated union: `CandleSpec`, `LineSpec`, `IndicatorOverlaySpec`, `PerformanceSpec`.
     - `RenderMarkdownArgs(markdown: str, title: str | None = None)`
     - `MakeReportArgs(format: Literal["html","pdf","xlsx","pptx"], title: str, sections: list[ReportSection])`
   - Each tool exposes:
     - `name: str` (snake_case)
     - `description: str` (short, model-facing)
     - `args_schema: type[BaseModel]`
     - `async def run(args) -> ToolResult` where `ToolResult` is `{ "content": Any, "side_effects": list[SideEffect] }`. Side effects are events to emit to the UI (e.g. `chart_ready`, `artifact_ready`).
   - Tool registry: `TOOLS: dict[str, Tool]` and `to_grok_tool_specs() -> list[dict]` producing the JSON schema the SDK expects.

2. `backend/app/services/grok/orchestrator.py`
   - `class Orchestrator`:
     - Holds `GrokClient` + tool registry.
     - `async def run(conversation_id, user_message) -> AsyncIterator[OrchestratorEvent]`:
       - Append user message.
       - Loop up to `settings.grok_max_tool_rounds`:
         - Call `grok.chat_stream(messages, tools=TOOLS)`.
         - As tokens arrive, yield `{"type":"token","text":...}`.
         - As tool calls finish, yield `{"type":"tool_call","name":...,"args":...}`, dispatch all in parallel with `asyncio.gather`, append `tool` messages, yield `{"type":"tool_result","name":...,"summary":...}`.
         - When the model returns a final response with no tool calls, yield `{"type":"done"}` and break.
       - For each tool side effect, yield `{"type":"chart"|"artifact",...}` so the UI can render immediately.
   - Per-conversation message stores: in-memory dict keyed by conversation_id (later: optional persistence under `data_dir`).

3. Tests
   - `backend/tests/unit/test_orchestrator.py` — fake `GrokClient` that scripts a 2-round tool-call sequence; assert event sequence.

## Constraints
- Tool runners must be fast and side-effect-light. Heavy work (chart rendering) happens in `services/reports/`.
- Tool errors surface as `tool_result` events with `error: True` so the model can recover.

## Acceptance
- Unit test for a scripted 2-round conversation passes.
- Manual run: orchestrator handles "Show AAPL 90-day chart with RSI" producing tool calls for `get_bars`, `compute_indicators`, `make_chart`, then `render_markdown` final.
