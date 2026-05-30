import type { DiagramData, DiagramLegendItem, DiagramTypeMeta, DiagramUiStrings } from "../api/client";
import DiagramLegend from "./DiagramLegend";
import MermaidDiagram from "./MermaidDiagram";

function resolveTitle(diagram: DiagramData, metaByType: Record<string, DiagramTypeMeta>): string {
  if (diagram.title?.trim()) return diagram.title.trim();
  return metaByType[diagram.diagram_type]?.default_title || diagram.diagram_type;
}

function resolveLegend(diagram: DiagramData, defaultLegend: DiagramLegendItem[]): DiagramLegendItem[] {
  if (diagram.legend?.length) return diagram.legend;
  return defaultLegend;
}

export default function DiagramCard({
  diagram,
  metaByType,
  defaultLegend,
  uiStrings,
  renderId,
}: {
  diagram: DiagramData;
  metaByType: Record<string, DiagramTypeMeta>;
  defaultLegend: DiagramLegendItem[];
  uiStrings: DiagramUiStrings;
  renderId: string;
}) {
  const title = resolveTitle(diagram, metaByType);
  const caption = diagram.caption?.trim() || metaByType[diagram.diagram_type]?.description || "";
  const legend = resolveLegend(diagram, defaultLegend);
  const nodes = (diagram.nodes || []) as Array<{
    id?: string;
    label?: string;
    risk?: string;
    confidence?: string;
    group?: string;
  }>;

  return (
    <section className="diagram-card" style={{ marginBottom: "2rem" }}>
      <h3 style={{ marginBottom: "0.35rem" }}>{title}</h3>
      {caption ? (
        <p style={{ color: "var(--muted)", fontSize: "0.92rem", marginTop: 0 }}>{caption}</p>
      ) : null}
      <DiagramLegend items={legend} />
      <MermaidDiagram code={diagram.mermaid} id={renderId} uiStrings={uiStrings} />
      {nodes.length > 0 ? (
        <details style={{ marginTop: "0.75rem" }}>
          <summary style={{ cursor: "pointer", color: "var(--muted)", fontSize: "0.9rem" }}>
            {uiStrings.node_summary_label}（{nodes.length}）
          </summary>
          <ul style={{ fontSize: "0.85rem", paddingLeft: "1.2rem" }}>
            {nodes.slice(0, 50).map((node, idx) => (
              <li key={node.id || idx}>
                {node.label || node.id}
                {node.risk ? ` · ${uiStrings.node_risk_prefix} ${node.risk}` : ""}
                {node.confidence ? ` · ${uiStrings.node_confidence_prefix} ${node.confidence}` : ""}
                {node.group && node.group !== "default" ? ` · ${node.group}` : ""}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
