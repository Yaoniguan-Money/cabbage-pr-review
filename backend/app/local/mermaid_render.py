from __future__ import annotations

import re

from app.models.schemas import DiagramData, GraphEdge, GraphNode, RiskLevel


RISK_CLASS = {
    RiskLevel.HIGH: ":::riskHigh",
    RiskLevel.MEDIUM: ":::riskMed",
    RiskLevel.LOW: ":::riskLow",
    None: "",
}

INVALID_ID = re.compile(r"[^a-zA-Z0-9_]")

# Mermaid flowchart 保留字（节点 ID 不可直接使用，见 mermaid-js #4182 / #4645）
RESERVED_NODE_IDS: frozenset[str] = frozenset(
    {
        "graph",
        "flowchart",
        "flowchart-v2",
        "flowchart_v2",
        "end",
        "class",
        "classdef",
        "style",
        "linkstyle",
        "click",
        "call",
        "subgraph",
        "default",
        "interpolate",
        "flowchart-tb",
        "flowchart-lr",
    }
)


def _safe_id(raw: str, fallback: str) -> str:
    value = INVALID_ID.sub("_", (raw or "").strip())
    if not value:
        return fallback
    if value[0].isdigit() or value.lower() in RESERVED_NODE_IDS:
        return f"n_{value}"
    return value


def _safe_label(raw: str) -> str:
    return (raw or "").replace('"', "'").replace("\n", " ").strip() or "未命名节点"


def _safe_edge_label(raw: str) -> str:
    text = (raw or "").replace("|", "/").replace('"', "'").replace("\n", " ").strip()
    if not text:
        return ""
    return f'|"{text}"|'


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
    id_map: dict[str, str] = {}
    for idx, node in enumerate(data.nodes[:40]):
        cls = RISK_CLASS.get(node.risk, "")
        nid = _safe_id(node.id, f"n_{idx}")
        id_map[node.id] = nid
        safe_label = _safe_label(node.label)
        lines.append(f'  {nid}["{safe_label}"]{cls}')
    for edge in data.edges[:60]:
        src = id_map.get(edge.source) or _safe_id(edge.source, "unknown_source")
        dst = id_map.get(edge.target) or _safe_id(edge.target, "unknown_target")
        lbl = _safe_edge_label(edge.label)
        lines.append(f"  {src} -->{lbl} {dst}")
    if len(data.nodes) == 0:
        lines.append('  empty["暂无结构数据"]')
    return "\n".join(lines)


def _render_path_compare(data: DiagramData) -> str:
    lines = [
        "flowchart LR",
        "subgraph before_nodes [变更前]",
    ]
    before_nodes = [n for n in data.nodes if n.group == "before"][:15]
    after_nodes = [n for n in data.nodes if n.group == "after"][:15]
    if not before_nodes and data.nodes:
        mid = max(1, len(data.nodes) // 2)
        before_nodes = data.nodes[:mid]
        after_nodes = data.nodes[mid:]
    id_map: dict[str, str] = {}
    for idx, n in enumerate(before_nodes):
        nid = _safe_id(n.id, f"b_{idx}")
        id_map[n.id] = nid
        lines.append(f'  {nid}["{_safe_label(n.label)}"]')
    lines.append("end")
    lines.append("subgraph after_nodes [变更后]")
    for idx, n in enumerate(after_nodes):
        nid = _safe_id(n.id, f"a_{idx}")
        id_map[n.id] = nid
        lines.append(f'  {nid}["{_safe_label(n.label)}"]')
    lines.append("end")
    for edge in data.edges[:20]:
        src = id_map.get(edge.source) or _safe_id(edge.source, "unknown_source")
        dst = id_map.get(edge.target) or _safe_id(edge.target, "unknown_target")
        lbl = _safe_edge_label(edge.label)
        lines.append(f"  {src} -->{lbl} {dst}")
    return "\n".join(lines)
