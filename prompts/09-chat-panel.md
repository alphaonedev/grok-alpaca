# Prompt 09 — Chat panel (streaming, tool-call aware, artifact sandbox)

## Goal
A first-class chat UI that streams Grok output and renders tool-call traces, inline charts, markdown, and HTML artifacts.

## Tasks
1. `src/components/chat/ChatPanel.tsx`
   - Conversation state in `zustand` (`useChatStore`): `messages: Message[]`, `conversationId: string`, `pending: boolean`.
   - On submit: call `streamSSE("/api/v1/chat", {conversation_id, message}, onEvent)`.
   - Event handling:
     - `token` → append to current assistant message (markdown buffer).
     - `tool_call` → push a `ToolCallBlock` (collapsible) with name + args (pretty-printed JSON).
     - `tool_result` → fill the matching `ToolCallBlock` with summary.
     - `chart` → render an inline chart via `<ChartHost chartSpec={...} />`.
     - `artifact` → render `<ArtifactFrame url={...} title={...} />` (iframe sandboxed).
     - `done` → mark message complete.
   - Conversation history persisted to `localStorage` keyed by conversation_id; "New chat" resets.

2. `src/components/chat/MarkdownRenderer.tsx`
   - `react-markdown` + `remark-gfm` + `rehype-highlight` + `remark-math` + `rehype-katex`.
   - Code blocks with copy button.
   - Tables get Tailwind styling.

3. `src/components/chat/ToolCallBlock.tsx`
   - Collapsed by default. Header shows tool name, status (running/done/error), and a chip with arg highlights (symbol, timeframe).
   - Expanded shows pretty JSON args + result summary.

4. `src/components/chat/ArtifactFrame.tsx`
   - `<iframe src={url} sandbox="allow-scripts" className="..."/>`
   - "Open in new tab" and "Download" buttons.

5. `src/components/chat/ChartHost.tsx`
   - Switches on `chart_spec.kind`:
     - `"candle"` → `<CandleChart>` (Lightweight Charts) from Prompt 10.
     - `"line" | "indicator_overlay"` → `<IndicatorPanel>` (Plotly-React).
     - `"performance"` → `<PerformanceChart>`.

6. `src/api/client.ts`
   - `streamSSE(url, body, onEvent)`: uses `fetch` with `body: JSON.stringify(body)` and a `ReadableStream` reader to parse `data: ...\n\n` chunks. Does **not** use the browser `EventSource` (which is GET-only).

7. Tests
   - `src/components/chat/ChatPanel.test.tsx` (vitest) — feeds a scripted stream into `streamSSE` and asserts DOM state transitions.

## Acceptance
- Send "Show AAPL daily for 60d with RSI" → tool-call blocks appear sequentially → an inline candle chart renders with RSI overlay → final markdown summary streams in.
- Refresh page → conversation restored from localStorage.
