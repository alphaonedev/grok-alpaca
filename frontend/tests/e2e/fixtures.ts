// Test fixtures: helpers for synthesizing API payloads used by the e2e suite.

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

/**
 * Build a deterministic, slowly trending series of daily bars for a symbol.
 * Stable values so visual snapshots / charts don't shift between runs.
 */
export function makeDailyBars(symbol: string, count = 30, start = 150): BarsResponse {
  const now = new Date();
  // Anchor to UTC midnight so timestamps are stable per day regardless of TZ.
  now.setUTCHours(0, 0, 0, 0);

  const bars: Bar[] = [];
  for (let i = count - 1; i >= 0; i--) {
    const ts = new Date(now);
    ts.setUTCDate(ts.getUTCDate() - i);
    const drift = (count - 1 - i) * 0.5; // gentle uptrend
    const open = start + drift;
    const close = open + 0.4;
    const high = close + 0.6;
    const low = open - 0.6;
    bars.push({
      timestamp: ts.toISOString(),
      open: round(open),
      high: round(high),
      low: round(low),
      close: round(close),
      volume: 1_000_000 + i * 1_000,
      vwap: round((open + close + high + low) / 4),
    });
  }

  return {
    symbol,
    timeframe: "1Day",
    lookback: "30D",
    count: bars.length,
    bars,
  };
}

export function makeSnapshot(symbol: string, lastClose = 168.3) {
  const now = new Date().toISOString();
  return {
    symbol,
    latest_trade: { price: lastClose + 0.25, ts: now, size: 100 },
    latest_quote: { bid: lastClose + 0.2, ask: lastClose + 0.3, ts: now },
    minute_bar: {
      timestamp: now,
      open: lastClose,
      high: lastClose + 0.4,
      low: lastClose - 0.2,
      close: lastClose + 0.25,
      volume: 50_000,
    },
    daily_bar: {
      timestamp: now,
      open: lastClose - 0.5,
      high: lastClose + 0.6,
      low: lastClose - 0.7,
      close: lastClose + 0.25,
      volume: 5_000_000,
    },
    previous_daily_bar: {
      timestamp: now,
      open: lastClose - 1,
      high: lastClose + 0.2,
      low: lastClose - 1.2,
      close: lastClose,
      volume: 4_800_000,
    },
  };
}

export function ssePayload(frames: Array<Record<string, unknown>>): string {
  return frames.map((f) => `data: ${JSON.stringify(f)}\n\n`).join("");
}

function round(n: number): number {
  return Math.round(n * 100) / 100;
}
