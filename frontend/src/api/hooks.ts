import { useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "./client";

export interface Bar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
}

export interface BarsResponse {
  symbol: string;
  timeframe: string;
  lookback: string;
  count: number;
  bars: Bar[];
}

export function useBars(symbol: string, timeframe: string, lookback: string) {
  return useQuery({
    queryKey: ["bars", symbol, timeframe, lookback],
    queryFn: () =>
      apiGet<BarsResponse>(
        `/api/v1/market/bars?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&lookback=${lookback}`
      ),
    enabled: !!symbol,
    staleTime: 60_000,
  });
}

export function useSnapshot(symbol: string) {
  return useQuery({
    queryKey: ["snapshot", symbol],
    queryFn: () => apiGet<Record<string, unknown>>(`/api/v1/market/snapshot/${encodeURIComponent(symbol)}`),
    enabled: !!symbol,
    refetchInterval: 10_000,
  });
}

export function useClock() {
  return useQuery({
    queryKey: ["clock"],
    queryFn: () => apiGet<{ is_open: boolean; next_open: string; next_close: string }>("/api/v1/market/clock"),
    refetchInterval: 30_000,
  });
}

export function useWatchlists() {
  return useQuery({
    queryKey: ["watchlists"],
    queryFn: () => apiGet<{ watchlists: { name: string; symbols: string[] }[] }>("/api/v1/watchlists"),
  });
}

export function useReports() {
  return useQuery({
    queryKey: ["reports"],
    queryFn: () => apiGet<{ reports: { id: string; title: string; format: string; url: string; created_at: string }[] }>("/api/v1/reports"),
    refetchInterval: 5_000,
  });
}

export async function addSymbol(name: string, symbol: string) {
  return apiPost(`/api/v1/watchlists/${encodeURIComponent(name)}/symbols`, { symbol });
}
