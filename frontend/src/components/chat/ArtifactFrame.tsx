interface Props {
  data: { id?: string; title?: string; format?: string; url?: string };
}

export function ArtifactFrame({ data }: Props) {
  const url = data.url || (data.id ? `/api/v1/reports/${data.id}` : undefined);
  return (
    <div className="my-2 border border-bg-line rounded-md overflow-hidden">
      <div className="px-3 py-1.5 text-xs flex items-center justify-between bg-bg-raised">
        <span>
          <span className="text-ink-accent">{data.format?.toUpperCase()}</span> · {data.title || "Artifact"}
        </span>
        {url && (
          <a href={url} target="_blank" rel="noopener noreferrer" className="text-ink-dim hover:text-ink underline">
            open
          </a>
        )}
      </div>
      {url && data.format === "html" && (
        <iframe
          src={url}
          sandbox="allow-scripts"
          className="w-full h-72 bg-bg-panel"
          title={data.title || "artifact"}
        />
      )}
    </div>
  );
}
