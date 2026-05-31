"""规则模式：四图确定性构建（复用 diagram_normalize / mermaid 链）。"""

from __future__ import annotations

from typing import Any

from app.local.diagram_meta import get_default_title
from app.local.diagram_normalize import build_global_compare_seed, normalize_diagrams
from app.models.schemas import (
    ConfidenceLevel,
    DiagramData,
    DiffCompareSchema,
    GraphEdge,
    GraphNode,
    ProjectIndexSchema,
    RiskLevel,
)
from app.rules.rule_schema import RuleHitRecord, map_severity


def _risk_rank(risk: RiskLevel | None) -> int:
    if risk == RiskLevel.HIGH:
        return 3
    if risk == RiskLevel.MEDIUM:
        return 2
    if risk == RiskLevel.LOW:
        return 1
    return 0


def _parse_architecture_seed(raw: Any) -> DiagramData | None:
    if not isinstance(raw, dict):
        return None
    try:
        payload = dict(raw)
        payload.setdefault("diagram_type", "architecture")
        seed = DiagramData.model_validate(payload)
        if seed.nodes:
            return seed
    except Exception:
        return None
    return None


def _hits_by_file(hits: list[RuleHitRecord]) -> dict[str, RiskLevel]:
    by_file: dict[str, RiskLevel] = {}
    for hit in hits:
        path = hit.file_path.replace("\\", "/")
        risk = map_severity(hit.severity)
        prev = by_file.get(path)
        if prev is None or _risk_rank(risk) > _risk_rank(prev):
            by_file[path] = risk
    return by_file


def _max_risk_for_path(path: str, hits_by_file: dict[str, RiskLevel]) -> RiskLevel | None:
    normalized = path.replace("\\", "/")
    if normalized in hits_by_file:
        return hits_by_file[normalized]
    for fp, risk in hits_by_file.items():
        if fp in normalized or normalized in fp:
            return risk
    return None


def _node_matches_path(node: GraphNode, file_path: str) -> bool:
    label = node.label.replace("\\", "/").lower()
    path = file_path.replace("\\", "/").lower()
    base = path.split("/")[-1]
    return path in label or label in path or base in label


def _build_architecture_diagram(
    pr_context: dict[str, Any],
    base_index: ProjectIndexSchema | None,
    head_index: ProjectIndexSchema | None,
) -> DiagramData | None:
    seed = _parse_architecture_seed(pr_context.get("architecture_seed"))
    if seed:
        if not seed.title:
            seed.title = get_default_title("architecture")
        return seed
    for index in (head_index, base_index):
        if index and index.architecture_diagram and index.architecture_diagram.nodes:
            diagram = index.architecture_diagram.model_copy(deep=True)
            if not diagram.title:
                diagram.title = get_default_title("architecture")
            return diagram
    return None


def _apply_file_risk_overlays(
    nodes: list[GraphNode],
    changed_paths: set[str],
    hits_by_file: dict[str, RiskLevel],
    pr_context: dict[str, Any],
) -> list[GraphNode]:
    file_to_node = pr_context.get("file_to_node") or {}
    if not isinstance(file_to_node, dict):
        file_to_node = {}
    node_by_id = {n.id: n for n in nodes}
    for path in changed_paths:
        risk = _max_risk_for_path(path, hits_by_file)
        if risk is None:
            continue
        mapped_id = file_to_node.get(path.replace("\\", "/"))
        if mapped_id and mapped_id in node_by_id:
            idx = next(i for i, n in enumerate(nodes) if n.id == mapped_id)
            prev = nodes[idx].risk
            if _risk_rank(risk) > _risk_rank(prev):
                nodes[idx] = nodes[idx].model_copy(update={"risk": risk})
            continue
        for idx, node in enumerate(nodes):
            if _node_matches_path(node, path):
                prev = node.risk
                if _risk_rank(risk) > _risk_rank(prev):
                    nodes[idx] = node.model_copy(update={"risk": risk})
    return nodes


def _build_impact_overlay(
    architecture: DiagramData | None,
    diff: DiffCompareSchema,
    hits: list[RuleHitRecord],
    pr_context: dict[str, Any],
) -> DiagramData | None:
    hits_by_file = _hits_by_file(hits)
    changed_paths = {a.file_path for a in diff.all_atoms if a.file_path}
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    if architecture and architecture.nodes:
        for node in architecture.nodes:
            nodes.append(
                GraphNode(
                    id=node.id,
                    label=node.label,
                    group=node.group or "module",
                    risk=node.risk,
                    confidence=node.confidence,
                )
            )
        edges = list(architecture.edges)
        nodes = _apply_file_risk_overlays(nodes, changed_paths, hits_by_file, pr_context)
    else:
        for idx, atom in enumerate(diff.all_atoms[:20]):
            if not atom.file_path:
                continue
            nodes.append(
                GraphNode(
                    id=f"impact_{idx}",
                    label=atom.file_path,
                    group="impact_changed",
                    risk=_max_risk_for_path(atom.file_path, hits_by_file),
                    confidence=ConfidenceLevel.MEDIUM,
                )
            )

    if not nodes:
        return None
    return DiagramData(
        diagram_type="impact_overlay",
        title=get_default_title("impact_overlay"),
        nodes=nodes,
        edges=edges,
    )


def _build_path_compare(
    pr_context: dict[str, Any],
    diff: DiffCompareSchema,
    hits: list[RuleHitRecord],
) -> DiagramData | None:
    focus = [str(p) for p in (pr_context.get("path_compare_focus") or []) if str(p).strip()]
    if not focus:
        focus = [a.file_path for a in diff.all_atoms[:5] if a.file_path]
    hits_by_file = _hits_by_file(hits)
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for idx, path in enumerate(focus[:5]):
        bid, aid = f"pc_b_{idx}", f"pc_a_{idx}"
        risk = _max_risk_for_path(path, hits_by_file)
        nodes.append(
            GraphNode(id=bid, label=path, group="before", confidence=ConfidenceLevel.HIGH)
        )
        nodes.append(
            GraphNode(
                id=aid,
                label=path,
                group="after",
                risk=risk,
                confidence=ConfidenceLevel.MEDIUM,
            )
        )
        edges.append(GraphEdge(source=bid, target=aid, label=""))
    if not nodes:
        return None
    return DiagramData(
        diagram_type="path_compare",
        title=get_default_title("path_compare"),
        nodes=nodes,
        edges=edges,
    )


def _build_global_compare_from_architecture(
    pr_context: dict[str, Any],
    diff: DiffCompareSchema,
    hits: list[RuleHitRecord],
) -> DiagramData | None:
    seed = _parse_architecture_seed(pr_context.get("architecture_seed"))
    if not seed or not seed.nodes:
        return None
    hits_by_file = _hits_by_file(hits)
    file_to_node = pr_context.get("file_to_node") or {}
    if not isinstance(file_to_node, dict):
        file_to_node = {}

    before_nodes: list[GraphNode] = []
    after_nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for node in seed.nodes:
        bid, aid = f"gc_b_{node.id}", f"gc_a_{node.id}"
        before_nodes.append(
            GraphNode(
                id=bid,
                label=node.label,
                group="before",
                confidence=node.confidence,
            )
        )
        risk = None
        for path, mapped_id in file_to_node.items():
            if mapped_id == node.id:
                risk = _max_risk_for_path(str(path), hits_by_file)
                if risk is not None:
                    break
        after_nodes.append(
            GraphNode(
                id=aid,
                label=node.label,
                group="after",
                risk=risk,
                confidence=node.confidence,
            )
        )
        edges.append(GraphEdge(source=bid, target=aid, label=""))
    return DiagramData(
        diagram_type="global_compare",
        title=get_default_title("global_compare"),
        nodes=before_nodes + after_nodes,
        edges=edges,
    )


def build_rules_diagrams(
    *,
    base_index: ProjectIndexSchema | None,
    head_index: ProjectIndexSchema | None,
    diff: DiffCompareSchema,
    hits: list[RuleHitRecord],
    pr_context: dict[str, Any],
) -> list[DiagramData]:
    architecture = _build_architecture_diagram(pr_context, base_index, head_index)
    impact = _build_impact_overlay(architecture, diff, hits, pr_context)
    global_cmp = _build_global_compare_from_architecture(pr_context, diff, hits)
    if global_cmp is None:
        global_cmp = build_global_compare_seed(
            base_index or ProjectIndexSchema(version="base"),
            head_index or ProjectIndexSchema(version="head"),
            diff,
        )
    if global_cmp and not global_cmp.title:
        global_cmp.title = get_default_title("global_compare")
    path_cmp = _build_path_compare(pr_context, diff, hits)

    raw: list[DiagramData] = []
    if architecture:
        raw.append(architecture)
    if impact:
        raw.append(impact)
    if global_cmp:
        raw.append(global_cmp)
    if path_cmp:
        raw.append(path_cmp)
    return normalize_diagrams(raw)
