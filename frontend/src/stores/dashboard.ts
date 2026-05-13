import { create } from "zustand";

interface DashboardState {
  activeSymbol: string;
  timeframe: "1Min" | "5Min" | "15Min" | "1Hour" | "1Day" | "1Week";
  lookback: string;
  indicators: string[];
  setSymbol: (s: string) => void;
  setTimeframe: (t: DashboardState["timeframe"]) => void;
  setLookback: (l: string) => void;
  toggleIndicator: (i: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  activeSymbol: "AAPL",
  timeframe: "1Day",
  lookback: "180d",
  indicators: ["SMA", "RSI"],
  setSymbol: (s) => set({ activeSymbol: s }),
  setTimeframe: (t) => set({ timeframe: t }),
  setLookback: (l) => set({ lookback: l }),
  toggleIndicator: (i) =>
    set((st) => ({
      indicators: st.indicators.includes(i) ? st.indicators.filter((x) => x !== i) : [...st.indicators, i],
    })),
}));
