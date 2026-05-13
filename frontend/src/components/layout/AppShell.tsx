import { useClock } from "@/api/hooks";
import { WatchList } from "@/components/watchlist/WatchList";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ChartCanvas } from "@/components/chart/ChartCanvas";
import { ReportsList } from "@/components/reports/ReportsList";
import { useState } from "react";
import { cn } from "@/lib/cn";

type Tab = "price" | "analysis" | "reports";

export function AppShell() {
  const clock = useClock();
  const [tab, setTab] = useState<Tab>("price");

  return (
    <div className="h-full grid grid-rows-[48px_1fr]">
      <header className="flex items-center justify-between border-b border-bg-line px-4 bg-bg-panel/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="text-ink-accent font-semibold tracking-wider">grok-alpaca</span>
          <span className="text-xs text-ink-dim">localhost financial analysis</span>
        </div>
        <div className="text-xs text-ink-dim flex items-center gap-3">
          <span className={cn("h-2 w-2 rounded-full", clock.data?.is_open ? "bg-up" : "bg-down")} />
          <span>{clock.data?.is_open ? "market open" : "market closed"}</span>
        </div>
      </header>

      <div className="grid grid-cols-[280px_1fr_420px] min-h-0">
        <aside className="border-r border-bg-line overflow-y-auto scrollbar-fine bg-bg-panel/40">
          <WatchList />
        </aside>

        <main className="min-w-0 flex flex-col">
          <nav className="flex gap-1 p-2 border-b border-bg-line">
            {(["price", "analysis", "reports"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "px-3 py-1.5 text-sm rounded-md",
                  tab === t ? "bg-bg-raised text-ink-accent" : "text-ink-dim hover:text-ink hover:bg-bg-raised/60"
                )}
              >
                {t}
              </button>
            ))}
          </nav>
          <div className="flex-1 min-h-0 overflow-y-auto scrollbar-fine">
            {tab === "price" && <ChartCanvas />}
            {tab === "analysis" && <div className="p-4 text-ink-dim text-sm">Analysis tab — ask Grok in the chat panel →</div>}
            {tab === "reports" && <ReportsList />}
          </div>
        </main>

        <aside className="border-l border-bg-line min-w-0 flex flex-col bg-bg-panel/40">
          <ChatPanel />
        </aside>
      </div>
    </div>
  );
}
