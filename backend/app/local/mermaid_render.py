from __future__ import annotations

from app.models.schemas import DiagramData, GraphEdge, GraphNode, RiskLevel


RISK_CLASS = {
    RiskLevel.HIGH: ":::riskHigh",
    RiskLevel.MEDIUM: ":::riskMed",
    RiskLevel.LOW: ":::riskLow",
    None: "",
}


def render_diagram(data: DiagramData) -> str:
    if data.diagram_type == "path_compare":
        return _render_path_compare(data)
    return _render_flowchart(data)


def _render_flowchart(data: DiagramData) -> str:
    lines = [
        "flowchart TB",
        "classDef riskHigh fill:#fee2e2,stroke:#dc2626",
        "classDef riskMed fill:#fef3c7,stroke:#d97706",
        "classDef riskLow fill:#dbeafe,stroke:#2563eb",
        "classDef default fill:#f3f4f6,stroke:#6b7280",
    ]
    for node in data.nodes[:40]:
        cls = RISK_CLASS.get(node.risk, "")
        safe_label = node.label.replace('"', "'")
        lines.append(f'  {node.id}["{safe_label}"]{cls}')
    for edge in data.edges[:60]:
        lbl = f"|{edge.label}|" if edge.label else ""
        lines.append(f"  {edge.source} -->{lbl} {edge.target}")
    if len(data.nodes) == 0:
        lines.append('  empty["暂无结构数据"]')
    return "\n".join(lines)


def _render_path_compare(data: DiagramData) -> str:
    lines = [
        "flowchart LR",
        "subgraph before [变更前]",
    ]
    before_nodes = [n for n in data.nodes if n.group == "before"][:15]
    after_nodes = [n for n in data.nodes if n.group == "after"][:15]
    if not before_nodes and data.nodes:
        mid = max(1, len(data.nodes) // 2)
        before_nodes = data.nodes[:mid]
        after_nodes = data.nodes[mid:]
    for n in before_nodes:
        lines.append(f'  {n.id}["{n.label.replace(chr(34), chr(39))}"]')
    lines.append("end")
    lines.append("subgraph after [变更后]")
    for n in after_nodes:
        lines.append(f'  {n.id}["{n.label.replace(chr(34), chr(39))}"]')
    lines.append("end")
    for edge in data.edges[:20]:
        lines.append(f"  {edge.source} --> {edge.target}")
    return "\n".join(lines)
