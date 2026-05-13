# Prompt 10 — Charts (Lightweight Charts + Plotly-React)

## Goal
Make charts feel finance-grade: smooth candles, crosshair, indicator overlays, theme matching the dark UI.

## Tasks
1. `src/components/chart/CandleChart.tsx`
   - Uses `lightweight-charts` v5.
   - Props: `bars: Bar[]`, `overlays?: SeriesOverlay[]`, `subplots?: SubplotSpec[]` (RSI/MACD in lower panel), `theme: "dark"`, `onCrosshairMove?: (price, time) => void`.
   - Volume histogram on secondary scale.
   - Auto-fit on first render; remember zoom on re-render with same symbol.

2. `src/components/chart/IndicatorPanel.tsx`
   - `react-plotly.js` — for any non-OHLC chart (RSI line, MACD histogram, correlation heatmap, returns distribution).
   - Dark Plotly theme: transparent paper, light text, gridlines at 8% opacity.

3. `src/components/chart/PerformanceChart.tsx`
   - Equity curve + drawdown shaded region.
   - Side stats card: total return, CAGR, Sharpe, max DD.

4. `src/components/chart/ChartCanvas.tsx`
   - The main center-pane container. Tabs: `Price | Indicators | Performance`. Driven by current symbol + timeframe in `useDashboardStore`.

5. `src/api/hooks/useBars.ts`
   - TanStack Query hook hitting `/api/v1/market/bars`. `staleTime: 60_000`. Disabled when symbol is empty.

6. `src/stores/dashboard.ts`
   - `useDashboardStore` (zustand): `activeSymbol`, `timeframe`, `indicators[]`, set/clear methods.

7. Tests
   - `src/components/chart/CandleChart.test.tsx` — snapshot + render-with-no-crash.

## Acceptance
- Click a symbol in watchlist → CandleChart loads within 200ms (warm cache).
- Switch timeframe → chart updates, indicators preserved.
- Crosshair tooltip shows OHLC + indicator values.
