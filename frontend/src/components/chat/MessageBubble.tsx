import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { ChartHost } from "@/components/chart/ChartHost";
import { ArtifactFrame } from "./ArtifactFrame";
import type { ChatMessage, ChatBlock } from "@/stores/chat";
import { cn } from "@/lib/cn";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[95%] rounded-lg px-3 py-2",
          isUser ? "bg-ink-accent/15 border border-ink-accent/30" : "bg-bg-raised/60 border border-bg-line"
        )}
      >
        {message.blocks.map((b, i) => (
          <Block key={i} block={b} />
        ))}
      </div>
    </div>
  );
}

function Block({ block }: { block: ChatBlock }) {
  if (block.type === "text" && block.content) {
    return (
      <div className="md-prose text-sm">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeHighlight, rehypeKatex]}
        >
          {block.content}
        </ReactMarkdown>
      </div>
    );
  }
  if (block.type === "markdown" && block.data?.markdown) {
    return (
      <div className="md-prose text-sm border-t border-bg-line pt-2 mt-2">
        <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeHighlight, rehypeKatex]}>
          {String(block.data.markdown)}
        </ReactMarkdown>
      </div>
    );
  }
  if (block.type === "tool_call") {
    return (
      <details className="my-1 text-xs">
        <summary className="cursor-pointer text-ink-dim hover:text-ink">
          <span className="font-mono text-ink-accent">{block.toolName}</span>
          {block.toolArgs && (
            <span className="text-ink-dim">
              {" "}
              ({Object.entries(block.toolArgs).slice(0, 3).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(", ")})
            </span>
          )}
          {block.done && <span className="text-up ml-2">✓</span>}
        </summary>
        <pre className="font-mono text-[10px] bg-bg-panel p-2 rounded mt-1 overflow-auto">
          {JSON.stringify({ args: block.toolArgs, summary: block.toolSummary }, null, 2)}
        </pre>
      </details>
    );
  }
  if (block.type === "chart" && block.data) {
    return <ChartHost spec={block.data as never} />;
  }
  if (block.type === "artifact" && block.data) {
    return <ArtifactFrame data={block.data} />;
  }
  if (block.type === "error") {
    return <div className="text-down text-xs my-1">⚠ {block.error}</div>;
  }
  return null;
}
