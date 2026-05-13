import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type ISeriesApi, type Time } from "lightweight-charts";
import type { Bar } from "@/api/hooks";

interface Props {
  bars: Bar[];
  overlays?: { name: string }[];
}

export function CandleChart({ bars }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: {
        background: { color: "transparent" },
        textColor: "#8a96ad",
      },
      grid: {
        vertLines: { color: "rgba(31,42,68,0.4)" },
        horzLines: { color: "rgba(31,42,68,0.4)" },
      },
      rightPriceScale: { borderColor: "#1f2a44" },
      timeScale: { borderColor: "#1f2a44", timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });
    chartRef.current = chart;
    candleRef.current = chart.addCandlestickSeries({
      upColor: "#23c08a",
      downColor: "#ff5d5d",
      borderUpColor: "#23c08a",
      borderDownColor: "#ff5d5d",
      wickUpColor: "#23c08a",
      wickDownColor: "#ff5d5d",
    });
    volRef.current = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "",
      color: "#1f2a44",
    });
    volRef.current.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });

    return () => chart.remove();
  }, []);

  useEffect(() => {
    if (!candleRef.current || !volRef.current) return;
    if (!bars.length) return;
    const candles = bars.map((b) => ({
      time: (Math.floor(new Date(b.timestamp).getTime() / 1000)) as Time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    const vols = bars.map((b) => ({
      time: (Math.floor(new Date(b.timestamp).getTime() / 1000)) as Time,
      value: b.volume,
      color: b.close >= b.open ? "rgba(35,192,138,0.4)" : "rgba(255,93,93,0.4)",
    }));
    candleRef.current.setData(candles);
    volRef.current.setData(vols);
    chartRef.current?.timeScale().fitContent();
  }, [bars]);

  return <div ref={ref} className="w-full h-full" />;
}
