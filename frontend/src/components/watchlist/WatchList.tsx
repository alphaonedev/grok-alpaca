import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWatchlists, addSymbol } from "@/api/hooks";
import { apiDelete } from "@/api/client";
import { useDashboardStore } from "@/stores/dashboard";
import { useStream } from "@/hooks/useWebSocket";
import { cn } from "@/lib/cn";

interface Tick {
  last?: number;
  prev?: number;
  ts?: string;
  flash?: "up" | "down" | null;
}

export function WatchList() {
  const { data } = useWatchlists();
  const setSymbol = useDashboardStore((s) => s.setSymbol);
  const activeSymbol = useDashboardStore((s) => s.activeSymbol);
  const [activeList, setActiveList] = useState<string>("Default");
  const [adding, setAdding] = useState("");
  const queryClient = useQueryClient();

  const list = data?.watchlists.find((w) => w.name === activeList) ?? data?.watchlists[0];
  const symbols = list?.symbols ?? [];

  const [ticks, setTicks] = useState<Record<string, Tick>>({});

  useStream(symbols, ["trades", "quotes"], (e) => {
    if (!e.symbol) return;
    setTicks((t) => {
      const prev = t[e.symbol!]?.last;
      const last = (e.kind === "trade" ? (e.data?.price as number) : (e.data?.bid as number)) ?? prev;
      const flash = prev != null && last != null ? (last > prev ? "up" : last < prev ? "down" : null) : null;
      return { ...t, [e.symbol!]: { last, prev, ts: e.data?.ts as string, flash } };
    });
  });

  useEffect(() => {
    const id = setInterval(() => {
      setTicks((t) => Object.fromEntries(Object.entries(t).map(([k, v]) => [k, { ...v, flash: null }])));
    }, 800);
    return () => clearInterval(id);
  }, []);

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!adding || !list) return;
    await addSymbol(list.name, adding.toUpperCase());
    setAdding("");
    queryClient.invalidateQueries({ queryKey: ["watchlists"] });
  }

  async function onRemove(sym: string) {
    if (!list) return;
    await apiDelete(`/api/v1/watchlists/${encodeURIComponent(list.name)}/symbols/${sym}`);
    queryClient.invalidateQueries({ queryKey: ["watchlists"] });
  }

  return (
    <div className="p-2">
      <div className="flex items-center justify-between px-2 py-1">
        <select
          value={activeList}
          onChange={(e) => setActiveList(e.target.value)}
          className="bg-transparent text-ink text-sm border border-bg-line rounded px-2 py-1"
        >
          {data?.watchlists.map((w) => (
            <option key={w.name} value={w.name} className="bg-bg-panel">
              {w.name}
            </option>
          ))}
        </select>
        <span className="text-xs text-ink-dim">{symbols.length}</span>
      </div>

      <form onSubmit={onAdd} className="flex gap-1 p-2">
        <input
          value={adding}
          onChange={(e) => setAdding(e.target.value)}
          placeholder="add symbol"
          className="flex-1 bg-bg-raised text-sm px-2 py-1 rounded border border-bg-line focus:outline-none focus:border-ink-accent"
        />
        <button type="submit" className="text-xs px-2 py-1 rounded bg-bg-raised hover:bg-bg-line">+</button>
      </form>

      <ul>
        {symbols.map((sym) => {
          const t = ticks[sym];
          return (
            <li
              key={sym}
              onClick={() => setSymbol(sym)}
              className={cn(
                "px-3 py-2 cursor-pointer flex items-center justify-between rounded border-l-2",
                sym === activeSymbol ? "border-ink-accent bg-bg-raised/60" : "border-transparent hover:bg-bg-raised/40",
                t?.flash === "up" && "tick-up",
                t?.flash === "down" && "tick-down"
              )}
            >
              <span className="font-mono text-sm">{sym}</span>
              <span className="flex items-center gap-2">
                <span className="font-mono text-xs text-ink-dim">{t?.last != null ? t.last.toFixed(2) : "—"}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(sym);
                  }}
                  className="text-ink-dim hover:text-down text-xs"
                >
                  ×
                </button>
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
