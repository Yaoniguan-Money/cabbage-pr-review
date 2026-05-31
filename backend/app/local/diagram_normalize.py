"""图表列表归一：按 SCHEMA_DIAGRAM_TYPES 顺序输出。"""

from __future__ import annotations

from app.local.diagram_meta import SCHEMA_DIAGRAM_TYPES, get_ui_strings
from app.local.diagram_utils import attach_mermaid_list
from app.models.schemas import (
    DiagramData,
    DiffCompareSchema,
    GraphEdge,
    GraphNode,
    ProjectIndexSchema,
    RiskLevel,
)


def normalize_diagrams(diagrams: list[DiagramData]) -> list[DiagramData]:
    by_type: dict[str, DiagramData] = {}
    for diagram in diagrams:
        dtype = diagram.diagram_type
        if dtype in SCHEMA_DIAGRAM_TYPES:
            by_type[dtype] = diagram
    ordered: list[DiagramData] = []
    for dtype in SCHEMA_DIAGRAM_TYPES:
        if dtype in by_type:
            ordered.append(by_type[dtype])
    return attach_mermaid_list(ordered)


normalize_diagrams_to_three = normalize_diagrams


def _module_has_diff(module: str, file_paths: set[str]) -> bool:
    if not module:
        return False
    for path in file_paths:
        if module in path or path in module:
            return True
    return False


def build_global_compare_seed(
    base: ProjectIndexSchema,
    head: ProjectIndexSchema,
    diff: DiffCompareSchema,
) -> DiagramData | None:
    """从 base/head 索引结构生成 global_compare seed（无业务关键词推断）。"""
    before_nodes: list[GraphNode] = []
    after_nodes: list[GraphNode] = []
    changed_paths = {a.file_path for a in diff.all_atoms if a.file_path}

    if base.architecture_diagram and base.architecture_diagram.nodes:
        for node in base.architecture_diagram.nodes:
            before_nodes.append(
                GraphNode(
                    id=node.id,
                    label=node.label,
                    group="before",
                    risk=node.risk,
                    confidence=node.confidence,
                )
            )
    else:
        for idx, module in enumerate(base.modules[:20]):
            before_nodes.append(GraphNode(id=f"base_m_{idx}", label=module, group="before"))
        for idx, entry in enumerate(base.entry_files[:5]):
            before_nodes.append(GraphNode(id=f"base_e_{idx}", label=entry, group="before"))

    if head.architecture_diagram and head.architecture_diagram.nodes:
        for node in head.architecture_diagram.nodes:
            after_nodes.append(
                GraphNode(
                    id=node.id,
                    label=node.label,
                    group="after",
                    risk=node.risk,
                    confidence=node.confidence,
                )
            )
    else:
        for idx, module in enumerate(head.modules[:20]):
            risk = RiskLevel.MEDIUM if _module_has_diff(module, changed_paths) else None
            after_nodes.append(
                GraphNode(id=f"head_m_{idx}", label=module, group="after", risk=risk)
            )
        for idx, entry in enumerate(head.entry_files[:5]):
            after_nodes.append(GraphNode(id=f"head_e_{idx}", label=entry, group="after"))

    if not before_nodes and not after_nodes:
        return None

    before_ids = {n.id for n in before_nodes}
    after_ids = {n.id for n in after_nodes}
    edges: list[GraphEdge] = []
    for node_id in before_ids & after_ids:
        edges.append(GraphEdge(source=node_id, target=node_id, label=""))

    return DiagramData(
        diagram_type="global_compare",
        nodes=before_nodes + after_nodes,
        edges=edges,
    )


def merge_diagram_seeds(
    agent5_diagrams: list[DiagramData],
    architecture_seed: DiagramData | None,
    impact_seed: DiagramData | None,
    global_seed: DiagramData | None = None,
) -> list[DiagramData]:
    by_type: dict[str, DiagramData] = {}
    for diagram in agent5_diagrams:
        by_type[diagram.diagram_type] = diagram
    if architecture_seed and "architecture" not in by_type:
        by_type["architecture"] = architecture_seed
    if impact_seed and "impact_overlay" not in by_type:
        by_type["impact_overlay"] = impact_seed
    if global_seed and "global_compare" not in by_type:
        by_type["global_compare"] = global_seed
    ordered: list[DiagramData] = []
    for dtype in SCHEMA_DIAGRAM_TYPES:
        if dtype in by_type:
            ordered.append(by_type[dtype])
    return ordered


def _has_before_after_groups(diagram: DiagramData) -> bool:
    if not diagram.nodes:
        return False
    groups = {n.group for n in diagram.nodes}
    return "before" in groups and "after" in groups


def collect_diagram_structural_notes(diagrams: list[DiagramData]) -> list[str]:
    ui = get_ui_strings()
    notes: list[str] = []
    for diagram in diagrams:
        if diagram.diagram_type == "path_compare" and diagram.nodes and not _has_before_after_groups(diagram):
            notes.append(ui.degradation_path_compare_missing_groups)
        if diagram.diagram_type == "global_compare" and diagram.nodes and not _has_before_after_groups(diagram):
            notes.append(ui.degradation_global_compare_missing_groups)
    return notes


def merge_degradation_notes(*note_lists: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for notes in note_lists:
        for note in notes:
            text = str(note).strip()
            if text and text not in seen:
                seen.add(text)
                merged.append(text)
    return merged
