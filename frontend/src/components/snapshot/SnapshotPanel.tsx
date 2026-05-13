import { useSnapshot } from "@/api/hooks";
import { cn } from "@/lib/cn";

interface Props {
  symbol: string;
}

interface SnapshotShape {
  latest_trade?: { price?: number; size?: number };
  latest_quote?: { ap?: number; bp?: number };
  minute_bar?: { open?: number; high?: number; low?: number; close?: number; volume?: number; vwap?: number };
  daily_bar?: {
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    volume?: number;
    vwap?: number;
  };
  previous_daily_bar?: { close?: number };
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
}

function fmt(n: number | undefined | null, digits = 2): string {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtInt(n: number | undefined | null): string {
  if (n == null || Number.isNaN(n)) return "—";
  return Math.round(n).toLocaleString();
}

export function SnapshotPanel({ symbol }: Props) {
  const { data, isLoading, error } = useSnapshot(symbol);
  const snap = (data ?? {}) as SnapshotShape;

  const last =
    snap.latest_trade?.price ??
    snap.minute_bar?.close ??
    snap.daily_bar?.close ??
    null;
  const prevClose = snap.previous_daily_bar?.close ?? null;
  const chg = last != null && prevClose != null ? last - prevClose : null;
  const chgPct = chg != null && prevClose ? (chg / prevClose) * 100 : null;
  const high = snap.daily_bar?.high ?? null;
  const low = snap.daily_bar?.low ?? null;
  const volume = snap.daily_bar?.volume ?? null;
  const vwap = snap.daily_bar?.vwap ?? snap.minute_bar?.vwap ?? null;
  const yrHi = snap.fifty_two_week_high ?? null;
  const yrLo = snap.fifty_two_week_low ?? null;

  if (isLoading && !data) {
    return <div className="text-ink-dim text-xs p-3">Loading snapshot…</div>;
  }
  if (error) {
    return <div className="text-down text-xs p-3">Snapshot error: {(error as Error).message}</div>;
  }

  const chgClass = chg == null ? "text-ink-dim" : chg >= 0 ? "text-up" : "text-down";

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 p-3 text-xs">
      <Field label="Last" value={`$${fmt(last)}`} mono />
      <Field label="Prev close" value={`$${fmt(prevClose)}`} mono />
      <Field
        label="Day chg"
        value={
          chg == null
            ? "—"
            : `${chg >= 0 ? "+" : ""}${fmt(chg)} (${chgPct != null ? `${chgPct >= 0 ? "+" : ""}${chgPct.toFixed(2)}%` : "—"})`
        }
        mono
        valueClass={chgClass}
      />
      <Field
        label="Day range"
        value={low != null && high != null ? `${fmt(low)} – ${fmt(high)}` : "—"}
        mono
      />
      <Field label="Volume" value={fmtInt(volume)} mono />
      <Field label="VWAP" value={vwap != null ? `$${fmt(vwap)}` : "—"} mono />
      <Field label="52w high" value={yrHi != null ? `$${fmt(yrHi)}` : "—"} mono />
      <Field label="52w low" value={yrLo != null ? `$${fmt(yrLo)}` : "—"} mono />
    </div>
  );
}

function Field({
  label,
  value,
  mono,
  valueClass,
}: {
  label: string;
  value: string;
  mono?: boolean;
  valueClass?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-2 min-w-0">
      <span className="text-ink-dim text-[10px] uppercase tracking-wide">{label}</span>
      <span className={cn("truncate", mono && "font-mono", valueClass ?? "text-ink")}>{value}</span>
    </div>
  );
}

export default SnapshotPanel;
