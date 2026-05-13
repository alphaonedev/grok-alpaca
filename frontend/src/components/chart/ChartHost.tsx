import { CandleChart } from "./CandleChart";
import type { Bar } from "@/api/hooks";

interface ChartSpec {
  kind: string;
  title?: string;
  symbol?: string;
  bars?: Bar[];
}

export function ChartHost({ spec }: { spec: ChartSpec }) {
  return (
    <div className="border border-bg-line rounded-md overflow-hidden bg-bg-raised/40 my-2">
      <div className="px-3 py-1.5 text-xs text-ink-dim border-b border-bg-line">
        {spec.title || spec.symbol || spec.kind}
      </div>
      <div className="h-64">
        {spec.bars && spec.bars.length > 0 ? (
          <CandleChart bars={spec.bars} />
        ) : (
          <div className="text-ink-dim text-sm p-4">No data</div>
        )}
      </div>
    </div>
  );
}
