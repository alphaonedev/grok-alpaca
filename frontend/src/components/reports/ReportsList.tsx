import { useReports } from "@/api/hooks";

export function ReportsList() {
  const { data, isLoading } = useReports();
  if (isLoading) return <div className="p-4 text-ink-dim text-sm">Loading…</div>;
  const reports = data?.reports ?? [];
  if (reports.length === 0) {
    return (
      <div className="p-6 text-ink-dim text-sm">
        No reports yet. Ask Grok to "generate a one-pager on AAPL" in the chat.
      </div>
    );
  }
  return (
    <div className="p-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
      {reports.map((r) => (
        <a
          key={r.id}
          href={r.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block border border-bg-line rounded-md p-3 bg-bg-raised/40 hover:bg-bg-raised hover:border-ink-accent/40 transition"
        >
          <div className="text-xs text-ink-accent uppercase tracking-wider mb-1">{r.format}</div>
          <div className="text-sm font-medium mb-1">{r.title}</div>
          <div className="text-xs text-ink-dim">{new Date(r.created_at).toLocaleString()}</div>
        </a>
      ))}
    </div>
  );
}
