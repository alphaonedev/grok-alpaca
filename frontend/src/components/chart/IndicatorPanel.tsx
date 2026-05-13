import { lazy, Suspense, useEffect, useRef, useState } from "react";
import type { PlotParams } from "react-plotly.js";

export interface IndicatorSeries {
  name: string;
  x: (string | number)[];
  y: number[];
  type?: "scatter" | "bar";
}

export interface IndicatorPanelProps {
  title?: string;
  series: IndicatorSeries[];
}

// Lazy-loaded wrapper that pairs react-plotly.js's factory with the minified
// plotly bundle so the heavy plotly module is fetched on demand.
const LazyPlot = lazy(async () => {
  const [{ default: createPlotlyComponent }, plotlyMod] = await Promise.all([
    import("react-plotly.js/factory"),
    import("plotly.js-dist-min"),
  ]);
  // plotly-dist-min exposes the namespace as the default export
  const plotly = (plotlyMod as { default?: object }).default ?? plotlyMod;
  const Plot = createPlotlyComponent(plotly as object);
  return { default: Plot as React.ComponentType<PlotParams> };
});

const DARK_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#e6edf7", family: "JetBrains Mono, ui-monospace, monospace" },
  margin: { l: 48, r: 16, t: 28, b: 36 },
  xaxis: {
    gridcolor: "#1f2a44",
    zerolinecolor: "#1f2a44",
    linecolor: "#1f2a44",
    tickfont: { color: "#8a96ad" },
  },
  yaxis: {
    gridcolor: "#1f2a44",
    zerolinecolor: "#1f2a44",
    linecolor: "#1f2a44",
    tickfont: { color: "#8a96ad" },
  },
  legend: {
    orientation: "h" as const,
    y: 1.12,
    font: { color: "#8a96ad", size: 10 },
    bgcolor: "rgba(0,0,0,0)",
  },
} as const;

const PALETTE = ["#8fb6ff", "#23c08a", "#ff5d5d", "#f1c84b", "#b89cff", "#5ec8ff"];

export function IndicatorPanel({ title, series }: IndicatorPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      setSize({ w: el.clientWidth, h: el.clientHeight });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const data: PlotParams["data"] = series.map((s, i) => ({
    name: s.name,
    x: s.x,
    y: s.y,
    type: s.type ?? "scatter",
    mode: s.type === "bar" ? undefined : "lines",
    line: { color: PALETTE[i % PALETTE.length], width: 1.5 },
    marker: { color: PALETTE[i % PALETTE.length] },
    hoverlabel: { bgcolor: "#0f1828", bordercolor: "#1f2a44" },
  }));

  const layout: PlotParams["layout"] = {
    ...DARK_LAYOUT,
    title: title ? { text: title, font: { color: "#e6edf7", size: 13 } } : undefined,
    autosize: true,
    width: size.w || undefined,
    height: size.h || undefined,
    showlegend: series.length > 1,
  };

  return (
    <div ref={containerRef} className="w-full h-full">
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
  );
}

export default IndicatorPanel;
