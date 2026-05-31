from __future__ import annotations

import re
from collections import Counter

from app.local.diagram_meta import (
    MAX_ARCHITECTURE_EDGES,
    MAX_ARCHITECTURE_NODES,
    MAX_GLOBAL_EDGES,
    MAX_GLOBAL_NODES_PER_GROUP,
    MAX_IMPACT_EDGES,
    MAX_IMPACT_NODES,
    MAX_PATH_EDGES,
    MAX_PATH_NODES_PER_GROUP,
    RESERVED_NODE_IDS,
    build_class_defs,
    get_confidence_suffix,
    get_entry_style,
    get_global_after_style,
    get_global_before_style,
    get_risk_style,
    get_ui_strings,
)
from app.models.schemas import ConfidenceLevel, DiagramData, GraphEdge, GraphNode, RiskLevel

INVALID_ID = re.compile(r"[^a-zA-Z0-9_]")
_UI = get_ui_strings()


def _risk_class(risk: RiskLevel | None) -> str:
    token = get_risk_style(risk)
    return f":::{token.class_name}"


def _safe_id(raw: str, fallback: str) -> str:
    value = INVALID_ID.sub("_", (raw or "").strip())
    if not value:
        return fallback
    if value[0].isdigit() or value.lower() in RESERVED_NODE_IDS:
        return f"n_{value}"
    return value


def _safe_label(raw: str, confidence: ConfidenceLevel | None = None) -> str:
    base = (raw or "").replace('"', "'").replace("\n", " ").strip() or _UI.unnamed_node
    suffix = get_confidence_suffix(confidence)
    if suffix:
        return f"{base} ({suffix})"
    return base


def _safe_edge_label(raw: str) -> str:
    text = (raw or "").replace("|", "/").replace('"', "'").replace("\n", " ").strip()
    if not text:
        return ""
    return f'|"{text}"|'


def _node_style_class(node: GraphNode, *, for_impact: bool = False) -> str:
    if node.group == "entry":
        return f":::{get_entry_style().class_name}"
    if node.risk is not None:
        return _risk_class(node.risk)
    return f":::{get_risk_style(None).class_name}"


def _global_node_style_class(node: GraphNode) -> str:
    if node.group == "entry":
        return f":::{get_entry_style().class_name}"
    if node.group == "before":
        return f":::{get_global_before_style().class_name}"
    if node.risk is not None:
        return _risk_class(node.risk)
    if node.group == "after":
        return f":::{get_global_after_style().class_name}"
    return f":::{get_risk_style(None).class_name}"


def _rank_nodes(nodes: list[GraphNode], edges: list[GraphEdge], limit: int) -> list[GraphNode]:
    if len(nodes) <= limit:
        return nodes
    degree: Counter[str] = Counter()
    for edge in edges:
        degree[edge.source] += 1
        degree[edge.target] += 1
    risk_weight = {RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1, None: 0}

    def score(node: GraphNode) -> tuple[int, int]:
        return (risk_weight.get(node.risk, 0), degree.get(node.id, 0))

    return sorted(nodes, key=score, reverse=True)[:limit]


def render_diagram(data: DiagramData) -> str:
    if data.diagram_type == "path_compare":
        return _render_path_compare(data)
    if data.diagram_type == "global_compare":
        return _render_global_compare(data)
    if data.diagram_type == "impact_overlay":
        return _render_impact_overlay(data)
    return _render_architecture(data)


def _render_architecture(data: DiagramData) -> str:
    lines = ["flowchart TB", *build_class_defs()]
    nodes = _rank_nodes(data.nodes, data.edges, MAX_ARCHITECTURE_NODES)
    id_map: dict[str, str] = {}
    for idx, node in enumerate(nodes):
        cls = _node_style_class(node)
        nid = _safe_id(node.id, f"n_{idx}")
        id_map[node.id] = nid
        safe_label = _safe_label(node.label, node.confidence)
        lines.append(f'  {nid}["{safe_label}"]{cls}')
    node_ids = set(id_map.keys())
    edge_count = 0
    for edge in data.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            continue
        if edge_count >= MAX_ARCHITECTURE_EDGES:
            break
        src = id_map[edge.source]
        dst = id_map[edge.target]
        lbl = _safe_edge_label(edge.label)
        lines.append(f"  {src} -->{lbl} {dst}")
        edge_count += 1
    if len(data.nodes) == 0:
        lines.append(f'  empty["{_UI.empty_structure}"]')
    return "\n".join(lines)


def _render_impact_overlay(data: DiagramData) -> str:
    lines = ["flowchart TB", *build_class_defs()]
    nodes = _rank_nodes(data.nodes, data.edges, MAX_IMPACT_NODES)
    changed = [n for n in nodes if n.risk is not None]
    unchanged = [n for n in nodes if n.risk is None]
    id_map: dict[str, str] = {}

    def render_node(node: GraphNode, idx: int, prefix: str) -> None:
        cls = _node_style_class(node, for_impact=True)
        nid = _safe_id(node.id, f"{prefix}_{idx}")
        id_map[node.id] = nid
        safe_label = _safe_label(node.label, node.confidence)
        lines.append(f'    {nid}["{safe_label}"]{cls}')

    if changed:
        lines.append(f"subgraph changed_area [{_UI.impact_changed_subgraph}]")
        for idx, node in enumerate(changed):
            render_node(node, idx, "c")
        lines.append("end")
    for idx, node in enumerate(unchanged):
        render_node(node, idx, "u")

    node_ids = set(id_map.keys())
    edge_count = 0
    for edge in data.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            continue
        if edge_count >= MAX_IMPACT_EDGES:
            break
        src = id_map[edge.source]
        dst = id_map[edge.target]
        lbl = _safe_edge_label(edge.label)
        lines.append(f"  {src} -->{lbl} {dst}")
        edge_count += 1
    if len(data.nodes) == 0:
        lines.append(f'  empty["{_UI.empty_structure}"]')
    return "\n".join(lines)


def _render_path_compare(data: DiagramData) -> str:
    lines = ["flowchart LR", *build_class_defs()]
    before_nodes = [n for n in data.nodes if n.group == "before"]
    after_nodes = [n for n in data.nodes if n.group == "after"]
    before_nodes = _rank_nodes(before_nodes, data.edges, MAX_PATH_NODES_PER_GROUP)
    after_nodes = _rank_nodes(after_nodes, data.edges, MAX_PATH_NODES_PER_GROUP)
    id_map: dict[str, str] = {}

    lines.append(f"subgraph before_nodes [{_UI.path_compare_before}]")
    for idx, node in enumerate(before_nodes):
        nid = _safe_id(node.id, f"b_{idx}")
        id_map[node.id] = nid
        lines.append(f'  {nid}["{_safe_label(node.label, node.confidence)}"]')
    lines.append("end")
    lines.append(f"subgraph after_nodes [{_UI.path_compare_after}]")
    for idx, node in enumerate(after_nodes):
        nid = _safe_id(node.id, f"a_{idx}")
        id_map[node.id] = nid
        lines.append(f'  {nid}["{_safe_label(node.label, node.confidence)}"]')
    lines.append("end")

    node_ids = set(id_map.keys())
    edge_count = 0
    for edge in data.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            continue
        if edge_count >= MAX_PATH_EDGES:
            break
        src = id_map[edge.source]
        dst = id_map[edge.target]
        lbl = _safe_edge_label(edge.label)
        lines.append(f"  {src} -->{lbl} {dst}")
        edge_count += 1
    if not before_nodes and not after_nodes:
        lines.append(f'  empty["{_UI.empty_structure}"]')
    return "\n".join(lines)


def _render_global_compare(data: DiagramData) -> str:
    lines = ["flowchart LR", *build_class_defs()]
    before_nodes = [n for n in data.nodes if n.group == "before"]
    after_nodes = [n for n in data.nodes if n.group == "after"]
    before_nodes = _rank_nodes(before_nodes, data.edges, MAX_GLOBAL_NODES_PER_GROUP)
    after_nodes = _rank_nodes(after_nodes, data.edges, MAX_GLOBAL_NODES_PER_GROUP)
    id_map: dict[str, str] = {}

    lines.append(f"subgraph global_before [{_UI.global_compare_before}]")
    for idx, node in enumerate(before_nodes):
        nid = _safe_id(node.id, f"gb_{idx}")
        id_map[node.id] = nid
        cls = _global_node_style_class(node)
        lines.append(f'  {nid}["{_safe_label(node.label, node.confidence)}"]{cls}')
    lines.append("end")
    lines.append(f"subgraph global_after [{_UI.global_compare_after}]")
    for idx, node in enumerate(after_nodes):
        nid = _safe_id(node.id, f"ga_{idx}")
        id_map[node.id] = nid
        cls = _global_node_style_class(node)
        lines.append(f'  {nid}["{_safe_label(node.label, node.confidence)}"]{cls}')
    lines.append("end")

    node_ids = set(id_map.keys())
    edge_count = 0
    for edge in data.edges:
        if edge.source not in node_ids or edge.target not in node_ids:
            continue
        if edge_count >= MAX_GLOBAL_EDGES:
            break
        src = id_map[edge.source]
        dst = id_map[edge.target]
        lbl = _safe_edge_label(edge.label)
        lines.append(f"  {src} -->{lbl} {dst}")
        edge_count += 1
    if not before_nodes and not after_nodes:
        lines.append(f'  empty["{_UI.empty_structure}"]')
    return "\n".join(lines)
