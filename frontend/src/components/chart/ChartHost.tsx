import { CandleChart } from "./CandleChart";
import { IndicatorPanel, type IndicatorSeries } from "./IndicatorPanel";
import { PerformanceChart, type EquityPoint, type PerformanceStats } from "./PerformanceChart";
import type { Bar } from "@/api/hooks";

// Bar columns that are NOT indicator overlays
const OHLCV_KEYS = new Set(["timestamp", "open", "high", "low", "close", "volume", "vwap"]);

interface ChartSpec {
  kind: string;
  title?: string;
  symbol?: string;
  bars?: Bar[];
  overlays?: { name: string }[];
  equity?: EquityPoint[];
  stats?: PerformanceStats;
}

function indicatorSeriesFromBars(bars: Bar[]): IndicatorSeries[] {
  if (!bars.length) return [];
  const x = bars.map((b) => b.timestamp);
  const keys = Object.keys(bars[0] as unknown as Record<string, unknown>).filter((k) => !OHLCV_KEYS.has(k));
  return keys.map((k) => ({
    name: k,
    x,
    y: bars.map((b) => Number((b as unknown as Record<string, unknown>)[k] ?? NaN)),
    type: "scatter" as const,
  }));
}

function closeSeriesFromBars(bars: Bar[]): IndicatorSeries[] {
  if (!bars.length) return [];
  return [
    {
      name: "close",
      x: bars.map((b) => b.timestamp),
      y: bars.map((b) => b.close),
      type: "scatter",
    },
  ];
}

export function ChartHost({ spec }: { spec: ChartSpec }) {
  const title = spec.title || spec.symbol || spec.kind;

  const renderBody = () => {
    if (spec.kind === "performance") {
      if (!spec.equity || !spec.stats) {
        return <div className="text-ink-dim text-sm p-4">No performance data</div>;
      }
      return <PerformanceChart equity={spec.equity} stats={spec.stats} />;
    }
    if (spec.kind === "indicator_overlay") {
      const series = indicatorSeriesFromBars(spec.bars ?? []);
      if (!series.length) return <div className="text-ink-dim text-sm p-4">No indicator series</div>;
      return <IndicatorPanel title={spec.title} series={series} />;
    }
    if (spec.kind === "line") {
      const series = closeSeriesFromBars(spec.bars ?? []);
      if (!series.length) return <div className="text-ink-dim text-sm p-4">No data</div>;
      return <IndicatorPanel title={spec.title} series={series} />;
    }
    // default → candle
    if (spec.bars && spec.bars.length > 0) {
      return <CandleChart bars={spec.bars} />;
    }
    return <div className="text-ink-dim text-sm p-4">No data</div>;
  };

  return (
    <div className="border border-bg-line rounded-md overflow-hidden bg-bg-raised/40 my-2">
      <div className="px-3 py-1.5 text-xs text-ink-dim border-b border-bg-line">{title}</div>
      <div className="h-64">{renderBody()}</div>
    </div>
  );
}
