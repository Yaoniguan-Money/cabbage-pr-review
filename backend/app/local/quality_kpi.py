"""基于 TaskResultSchema 字段的结构化质量 KPI，不做业务语义推断。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.local.diagram_meta import SCHEMA_DIAGRAM_TYPES


def _node_id_set(diagrams: list[Any], diagram_type: str) -> set[str]:
    for d in diagrams:
        if not isinstance(d, dict) or d.get("diagram_type") != diagram_type:
            continue
        ids: set[str] = set()
        for n in d.get("nodes") or []:
            if isinstance(n, dict) and n.get("id"):
                ids.add(str(n["id"]))
        return ids
    return set()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


@dataclass
class QualityMetrics:
    risks_count: int = 0
    degradation_notes_count: int = 0
    diagrams_count: int = 0
    diff_atoms_count: int = 0
    missing_info_count: int = 0
    diagram_has_mermaid: dict[str, bool] = field(default_factory=dict)
    diagram_node_counts: dict[str, int] = field(default_factory=dict)
    path_compare_has_before_after: bool = False
    global_compare_has_before_after: bool = False
    arch_impact_node_jaccard: float = 0.0
    risks_with_evidence_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "risks_count": self.risks_count,
            "degradation_notes_count": self.degradation_notes_count,
            "diagrams_count": self.diagrams_count,
            "diff_atoms_count": self.diff_atoms_count,
            "missing_info_count": self.missing_info_count,
            "diagram_has_mermaid": dict(self.diagram_has_mermaid),
            "diagram_node_counts": dict(self.diagram_node_counts),
            "path_compare_has_before_after": self.path_compare_has_before_after,
            "global_compare_has_before_after": self.global_compare_has_before_after,
            "arch_impact_node_jaccard": self.arch_impact_node_jaccard,
            "risks_with_evidence_count": self.risks_with_evidence_count,
            "risks_evidence_coverage": self.risks_evidence_coverage,
        }

    @property
    def risks_evidence_coverage(self) -> float:
        if self.risks_count == 0:
            return 1.0
        return self.risks_with_evidence_count / self.risks_count


@dataclass
class QualityThresholds:
    """阈值由调用方/配置文件传入，代码内不写 PR 或业务关键词。"""

    min_risks: int = 0
    max_degradation_notes: int = 0
    require_all_diagram_types: bool = True
    min_risks_evidence_coverage: float = 0.0
    require_missing_info_when_no_risks: bool = True
    min_diagrams_count: int = 0
    min_diagram_nodes: int = 0
    require_path_compare_groups: bool = False
    require_global_compare_groups: bool = False
    max_arch_impact_jaccard: float = 1.0


def compute_metrics(result: dict[str, Any]) -> QualityMetrics:
    """从任务结果 dict 计算指标（字段名与 TaskResultSchema 对齐）。"""
    risks = result.get("risks") or []
    diagrams = result.get("diagrams") or []
    degradation_notes = result.get("degradation_notes") or []
    diff_atoms = result.get("diff_atoms") or []
    missing_info = result.get("missing_info") or []

    diagram_has_mermaid: dict[str, bool] = {t: False for t in SCHEMA_DIAGRAM_TYPES}
    diagram_node_counts: dict[str, int] = {t: 0 for t in SCHEMA_DIAGRAM_TYPES}
    path_compare_has_before_after = False
    global_compare_has_before_after = False
    for d in diagrams:
        if not isinstance(d, dict):
            continue
        dtype = d.get("diagram_type")
        if dtype in diagram_has_mermaid:
            diagram_has_mermaid[str(dtype)] = bool((d.get("mermaid") or "").strip())
            nodes = d.get("nodes") or []
            if isinstance(nodes, list):
                diagram_node_counts[str(dtype)] = len(nodes)
            if dtype == "path_compare" and isinstance(nodes, list):
                groups = {
                    str(n.get("group"))
                    for n in nodes
                    if isinstance(n, dict) and n.get("group")
                }
                path_compare_has_before_after = "before" in groups and "after" in groups
            if dtype == "global_compare" and isinstance(nodes, list):
                groups = {
                    str(n.get("group"))
                    for n in nodes
                    if isinstance(n, dict) and n.get("group")
                }
                global_compare_has_before_after = "before" in groups and "after" in groups

    arch_ids = _node_id_set(diagrams, "architecture")
    impact_ids = _node_id_set(diagrams, "impact_overlay")
    arch_impact_jaccard = _jaccard(arch_ids, impact_ids)

    risks_with_evidence = sum(
        1 for r in risks if isinstance(r, dict) and bool((r.get("evidence") or "").strip())
    )

    return QualityMetrics(
        risks_count=len(risks),
        degradation_notes_count=len(degradation_notes),
        diagrams_count=len(diagrams),
        diff_atoms_count=len(diff_atoms),
        missing_info_count=len(missing_info),
        diagram_has_mermaid=diagram_has_mermaid,
        diagram_node_counts=diagram_node_counts,
        path_compare_has_before_after=path_compare_has_before_after,
        global_compare_has_before_after=global_compare_has_before_after,
        arch_impact_node_jaccard=arch_impact_jaccard,
        risks_with_evidence_count=risks_with_evidence,
    )


def evaluate_metrics(
    metrics: QualityMetrics,
    thresholds: QualityThresholds,
) -> tuple[bool, list[str]]:
    """按阈值评估，返回 (是否通过, 失败原因列表)。"""
    failures: list[str] = []

    if metrics.risks_count < thresholds.min_risks:
        failures.append(
            f"risks_count={metrics.risks_count} 低于阈值 min_risks={thresholds.min_risks}"
        )

    if metrics.degradation_notes_count > thresholds.max_degradation_notes:
        failures.append(
            f"degradation_notes_count={metrics.degradation_notes_count} "
            f"高于阈值 max_degradation_notes={thresholds.max_degradation_notes}"
        )

    if thresholds.require_all_diagram_types:
        for dtype in SCHEMA_DIAGRAM_TYPES:
            if not metrics.diagram_has_mermaid.get(dtype, False):
                failures.append(f"diagram_type={dtype} 缺少非空 mermaid")

    if metrics.risks_evidence_coverage < thresholds.min_risks_evidence_coverage:
        failures.append(
            f"risks_evidence_coverage={metrics.risks_evidence_coverage:.2f} "
            f"低于阈值 min_risks_evidence_coverage={thresholds.min_risks_evidence_coverage}"
        )

    if thresholds.min_diagrams_count and metrics.diagrams_count < thresholds.min_diagrams_count:
        failures.append(
            f"diagrams_count={metrics.diagrams_count} 低于阈值 min_diagrams_count={thresholds.min_diagrams_count}"
        )

    if thresholds.min_diagram_nodes > 0:
        for dtype in SCHEMA_DIAGRAM_TYPES:
            count = metrics.diagram_node_counts.get(dtype, 0)
            if count < thresholds.min_diagram_nodes:
                failures.append(
                    f"diagram_type={dtype} 节点数 {count} 低于 min_diagram_nodes={thresholds.min_diagram_nodes}"
                )

    if thresholds.require_path_compare_groups and not metrics.path_compare_has_before_after:
        failures.append("path_compare 缺少 before 与 after 分组节点")

    if thresholds.require_global_compare_groups and not metrics.global_compare_has_before_after:
        failures.append("global_compare 缺少 before 与 after 分组节点")

    if (
        thresholds.max_arch_impact_jaccard < 1.0
        and metrics.arch_impact_node_jaccard > thresholds.max_arch_impact_jaccard
    ):
        failures.append(
            f"arch_impact_node_jaccard={metrics.arch_impact_node_jaccard:.2f} "
            f"高于阈值 max_arch_impact_jaccard={thresholds.max_arch_impact_jaccard}"
        )

    if (
        thresholds.require_missing_info_when_no_risks
        and metrics.risks_count == 0
        and metrics.diff_atoms_count > 0
        and metrics.missing_info_count == 0
        and metrics.degradation_notes_count == 0
    ):
        failures.append(
            "存在 diff_atoms 但 risks 为空，且 missing_info 与 degradation_notes 均未说明原因"
        )

    return len(failures) == 0, failures
