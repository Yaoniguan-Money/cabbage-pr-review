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
    <section className="diagram-card">
      <h3>{title}</h3>
      {caption ? <p className="section-hint">{caption}</p> : null}
      <DiagramLegend items={legend} />
      <MermaidDiagram code={diagram.mermaid} id={renderId} uiStrings={uiStrings} />
      {nodes.length > 0 ? (
        <details className="diagram-details">
          <summary>
            {uiStrings.node_summary_label}（{nodes.length}）
          </summary>
          <ul>
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
