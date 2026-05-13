import { useState, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chat";
import { streamSSE, type SseEvent } from "@/api/client";
import { MessageBubble } from "./MessageBubble";

export function ChatPanel() {
  const { messages, conversationId, pending, pushMessage, appendBlock, patchBlock, appendToken, setPending, newConversation } =
    useChatStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function onSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || pending) return;
    const userMsgId = `u-${Date.now()}`;
    const asstMsgId = `a-${Date.now()}`;
    pushMessage({ id: userMsgId, role: "user", blocks: [{ type: "text", content: input }], createdAt: Date.now() });
    pushMessage({ id: asstMsgId, role: "assistant", blocks: [], createdAt: Date.now() });
    const userText = input;
    setInput("");
    setPending(true);
    try {
      await streamSSE(
        "/api/v1/chat",
        { conversation_id: conversationId, message: userText },
        (evt: SseEvent) => {
          if (evt.type === "token") {
            appendToken(asstMsgId, evt.text);
          } else if (evt.type === "tool_call") {
            appendBlock(asstMsgId, {
              type: "tool_call",
              toolName: evt.name,
              toolArgs: evt.arguments,
            });
          } else if (evt.type === "tool_result") {
            patchBlock(
              asstMsgId,
              (b) => b.type === "tool_call" && b.toolName === evt.name && b.toolSummary === undefined,
              { toolSummary: evt.summary, done: true }
            );
          } else if (evt.type === "chart") {
            appendBlock(asstMsgId, { type: "chart", data: evt.data });
          } else if (evt.type === "artifact") {
            appendBlock(asstMsgId, { type: "artifact", data: evt.data });
          } else if (evt.type === "markdown") {
            appendBlock(asstMsgId, { type: "markdown", data: evt.data });
          } else if (evt.type === "error") {
            appendBlock(asstMsgId, { type: "error", error: evt.error });
          }
        }
      );
    } catch (err) {
      appendBlock(asstMsgId, { type: "error", error: String(err) });
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-2 border-b border-bg-line">
        <span className="text-xs text-ink-dim">grok analyst · {conversationId.slice(0, 12)}</span>
        <button
          onClick={newConversation}
          className="text-xs px-2 py-1 rounded text-ink-dim hover:bg-bg-raised hover:text-ink"
        >
          New chat
        </button>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-fine p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-ink-dim text-sm">
            Try: <span className="font-mono">"Analyze NVDA with RSI and MACD over 90 days"</span>
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {pending && <div className="text-ink-dim text-xs">…</div>}
      </div>
      <form onSubmit={onSend} className="border-t border-bg-line p-2 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Grok about a symbol…"
          disabled={pending}
          className="flex-1 bg-bg-raised text-sm px-3 py-2 rounded border border-bg-line focus:outline-none focus:border-ink-accent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={pending}
          className="px-3 py-2 text-sm rounded bg-ink-accent text-bg-panel font-medium disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
