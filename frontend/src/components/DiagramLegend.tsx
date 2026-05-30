export interface DiagramLegendItem {
  key: string;
  label: string;
  color: string;
}

export default function DiagramLegend({ items }: { items: DiagramLegendItem[] }) {
  if (!items.length) return null;
  return (
    <div className="diagram-legend" style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "0.75rem" }}>
      {items.map((item) => (
        <span key={item.key} style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem", fontSize: "0.85rem" }}>
          <span
            aria-hidden
            style={{
              width: "0.75rem",
              height: "0.75rem",
              borderRadius: "2px",
              background: item.color || "var(--muted)",
              border: "1px solid var(--border)",
            }}
          />
          {item.label}
        </span>
      ))}
    </div>
  );
}
