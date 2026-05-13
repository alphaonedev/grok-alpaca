import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface ChatBlock {
  type: "text" | "tool_call" | "chart" | "artifact" | "markdown" | "error";
  content?: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolSummary?: unknown;
  data?: Record<string, unknown>;
  error?: string;
  done?: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  blocks: ChatBlock[];
  createdAt: number;
}

interface ChatState {
  conversationId: string;
  messages: ChatMessage[];
  pending: boolean;
  pushMessage: (m: ChatMessage) => void;
  appendBlock: (msgId: string, block: ChatBlock) => void;
  patchBlock: (msgId: string, predicate: (b: ChatBlock) => boolean, patch: Partial<ChatBlock>) => void;
  appendToken: (msgId: string, text: string) => void;
  setPending: (p: boolean) => void;
  newConversation: () => void;
}

const newId = () => `c-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      conversationId: newId(),
      messages: [],
      pending: false,
      pushMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
      appendBlock: (msgId, block) =>
        set((s) => ({
          messages: s.messages.map((m) => (m.id === msgId ? { ...m, blocks: [...m.blocks, block] } : m)),
        })),
      patchBlock: (msgId, predicate, patch) =>
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === msgId
              ? { ...m, blocks: m.blocks.map((b) => (predicate(b) ? { ...b, ...patch } : b)) }
              : m
          ),
        })),
      appendToken: (msgId, text) =>
        set((s) => ({
          messages: s.messages.map((m) => {
            if (m.id !== msgId) return m;
            const last = m.blocks[m.blocks.length - 1];
            if (last && last.type === "text") {
              return {
                ...m,
                blocks: [...m.blocks.slice(0, -1), { ...last, content: (last.content ?? "") + text }],
              };
            }
            return { ...m, blocks: [...m.blocks, { type: "text", content: text }] };
          }),
        })),
      setPending: (p) => set({ pending: p }),
      newConversation: () => set({ conversationId: newId(), messages: [] }),
    }),
    { name: "grok-alpaca:chat" }
  )
);
