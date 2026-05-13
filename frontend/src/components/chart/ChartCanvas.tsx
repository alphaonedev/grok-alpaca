import { useDashboardStore } from "@/stores/dashboard";
import { useBars, useSnapshot } from "@/api/hooks";
import { CandleChart } from "./CandleChart";
import { cn } from "@/lib/cn";

const TIMEFRAMES = ["1Min", "5Min", "15Min", "1Hour", "1Day", "1Week"] as const;
const LOOKBACKS = ["5d", "30d", "90d", "180d", "1y", "5y"] as const;

export function ChartCanvas() {
  const { activeSymbol, timeframe, lookback, setTimeframe, setLookback } = useDashboardStore();
  const bars = useBars(activeSymbol, timeframe, lookback);
  const snap = useSnapshot(activeSymbol);

  const latestClose = bars.data?.bars.at(-1)?.close;
  const prev = (snap.data as { previous_daily_bar?: { close: number } } | undefined)?.previous_daily_bar?.close;
  const dayChg = latestClose != null && prev != null ? ((latestClose - prev) / prev) * 100 : null;

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-wrap items-center gap-3 p-3 border-b border-bg-line">
        <div>
          <div className="text-2xl font-semibold font-mono">{activeSymbol}</div>
          <div className="text-xs text-ink-dim">
            {latestClose != null ? `$${latestClose.toFixed(2)}` : "—"}{" "}
            {dayChg != null && (
              <span className={dayChg >= 0 ? "text-up" : "text-down"}>
                {dayChg >= 0 ? "▲" : "▼"} {dayChg.toFixed(2)}%
              </span>
            )}
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1">
          {TIMEFRAMES.map((t) => (
            <button
              key={t}
              onClick={() => setTimeframe(t)}
              className={cn(
                "text-xs px-2 py-1 rounded",
                t === timeframe ? "bg-bg-raised text-ink-accent" : "text-ink-dim hover:bg-bg-raised/60"
              )}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1">
          {LOOKBACKS.map((l) => (
            <button
              key={l}
              onClick={() => setLookback(l)}
              className={cn(
                "text-xs px-2 py-1 rounded",
                l === lookback ? "bg-bg-raised text-ink-accent" : "text-ink-dim hover:bg-bg-raised/60"
              )}
            >
              {l}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-0 p-2">
        {bars.isLoading ? (
          <div className="text-ink-dim text-sm p-4">Loading bars…</div>
        ) : bars.error ? (
          <div className="text-down text-sm p-4">Error: {(bars.error as Error).message}</div>
        ) : (
          <CandleChart bars={bars.data?.bars ?? []} />
        )}
      </div>
    </div>
  );
}
