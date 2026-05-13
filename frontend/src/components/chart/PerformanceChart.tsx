import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { PlotParams } from "react-plotly.js";

export interface PerformanceStats {
  total_return: number;
  sharpe: number;
  max_drawdown: number;
  cagr?: number;
}

export interface EquityPoint {
  t: string;
  v: number;
}

export interface PerformanceChartProps {
  equity: EquityPoint[];
  stats: PerformanceStats;
}

const LazyPlot = lazy(async () => {
  const [{ default: createPlotlyComponent }, plotlyMod] = await Promise.all([
    import("react-plotly.js/factory"),
    import("plotly.js-dist-min"),
  ]);
  const plotly = (plotlyMod as { default?: object }).default ?? plotlyMod;
  const Plot = createPlotlyComponent(plotly as object);
  return { default: Plot as React.ComponentType<PlotParams> };
});

function fmtPct(n: number | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(2)}%`;
}

function fmtNum(n: number | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toFixed(2);
}

function computeDrawdown(equity: EquityPoint[]): number[] {
  let peak = -Infinity;
  return equity.map((p) => {
    if (p.v > peak) peak = p.v;
    if (peak <= 0) return 0;
    return (p.v - peak) / peak;
  });
}

export function PerformanceChart({ equity, stats }: PerformanceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { xs, eq, dd } = useMemo(() => {
    const xs = equity.map((p) => p.t);
    const eq = equity.map((p) => p.v);
    const dd = computeDrawdown(equity);
    return { xs, eq, dd };
  }, [equity]);

  const data: PlotParams["data"] = [
    {
      x: xs,
      y: eq,
      type: "scatter",
      mode: "lines",
      name: "Equity",
      line: { color: "#8fb6ff", width: 1.6 },
      hoverlabel: { bgcolor: "#0f1828", bordercolor: "#1f2a44" },
    },
    {
      x: xs,
      y: dd,
      type: "scatter",
      mode: "lines",
      name: "Drawdown",
      xaxis: "x2",
      yaxis: "y2",
      fill: "tozeroy",
      line: { color: "#ff5d5d", width: 1 },
      fillcolor: "rgba(255,93,93,0.15)",
      hoverlabel: { bgcolor: "#0f1828", bordercolor: "#1f2a44" },
    },
  ];

  const layout: PlotParams["layout"] = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: "#e6edf7", family: "JetBrains Mono, ui-monospace, monospace" },
    margin: { l: 56, r: 16, t: 24, b: 32 },
    autosize: true,
    width: size.w || undefined,
    height: size.h || undefined,
    showlegend: false,
    grid: { rows: 2, columns: 1, pattern: "independent", roworder: "top to bottom" },
    xaxis: {
      gridcolor: "#1f2a44",
      linecolor: "#1f2a44",
      tickfont: { color: "#8a96ad" },
      domain: [0, 1],
      anchor: "y",
    },
    yaxis: {
      gridcolor: "#1f2a44",
      linecolor: "#1f2a44",
      tickfont: { color: "#8a96ad" },
      title: { text: "Equity", font: { color: "#8a96ad", size: 11 } },
      domain: [0.42, 1],
    },
    xaxis2: {
      gridcolor: "#1f2a44",
      linecolor: "#1f2a44",
      tickfont: { color: "#8a96ad" },
      domain: [0, 1],
      anchor: "y2",
    },
    yaxis2: {
      gridcolor: "#1f2a44",
      linecolor: "#1f2a44",
      tickfont: { color: "#8a96ad" },
      tickformat: ".0%",
      title: { text: "Drawdown", font: { color: "#8a96ad", size: 11 } },
      domain: [0, 0.34],
    },
  };

  return (
    <div className="w-full h-full flex gap-3">
      <div ref={containerRef} className="flex-1 min-w-0">
        <Suspense fallback={<div className="text-ink-dim text-xs p-3">loading chart…</div>}>
          <LazyPlot
            data={data}
            layout={layout}
            config={{ displayModeBar: false, responsive: true }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        </Suspense>
      </div>
      <div className="w-40 shrink-0 bg-bg-raised/40 border border-bg-line rounded-md p-3 space-y-2 text-xs">
        <Stat label="Total return" value={fmtPct(stats.total_return)} accent={stats.total_return >= 0 ? "up" : "down"} />
        <Stat label="Sharpe" value={fmtNum(stats.sharpe)} />
        <Stat label="Max drawdown" value={fmtPct(stats.max_drawdown)} accent="down" />
        <Stat label="CAGR" value={fmtPct(stats.cagr)} />
      </div>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: "up" | "down" }) {
  const cls = accent === "up" ? "text-up" : accent === "down" ? "text-down" : "text-ink";
  return (
    <div>
      <div className="text-ink-dim uppercase tracking-wide text-[10px]">{label}</div>
      <div className={`font-mono ${cls}`}>{value}</div>
    </div>
  );
}

export default PerformanceChart;
