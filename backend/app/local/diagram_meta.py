"""图表元数据：标题、样式、UI 文案与 Agent 指令的唯一数据源。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models.schemas import ConfidenceLevel, DiagramData, RiskLevel

DiagramType = Literal["architecture", "impact_overlay", "global_compare", "path_compare"]

SCHEMA_DIAGRAM_TYPES: tuple[DiagramType, ...] = (
    "architecture",
    "impact_overlay",
    "global_compare",
    "path_compare",
)


@dataclass(frozen=True)
class StyleToken:
    class_name: str
    fill: str
    stroke: str
    label: str


@dataclass(frozen=True)
class DiagramTypeMeta:
    id: DiagramType
    default_title: str
    description: str
    layout: Literal["flowchart_tb", "flowchart_lr", "impact_subgraph", "global_compare_lr"]
    agent_semantics: str


@dataclass(frozen=True)
class UiStrings:
    section_label: str
    section_preview_label: str
    empty_diagrams: str
    unnamed_node: str
    empty_structure: str
    empty_export: str
    path_compare_before: str
    path_compare_after: str
    global_compare_before: str
    global_compare_after: str
    impact_changed_subgraph: str
    render_error_title: str
    render_error_hint: str
    confidence_suffix_high: str
    confidence_suffix_medium: str
    confidence_suffix_low: str
    degradation_path_compare_missing_groups: str
    degradation_global_compare_missing_groups: str
    node_summary_label: str
    node_risk_prefix: str
    node_confidence_prefix: str


_UI = UiStrings(
    section_label="四张图",
    section_preview_label="四张图（预览）",
    empty_diagrams="暂无图表",
    unnamed_node="未命名节点",
    empty_structure="暂无结构数据",
    empty_export="flowchart TB\n  empty[暂无数据]",
    path_compare_before="变更前",
    path_compare_after="变更后",
    global_compare_before="变更前架构",
    global_compare_after="变更后架构",
    impact_changed_subgraph="变更区域",
    render_error_title="图表渲染失败",
    render_error_hint="展开查看原始 Mermaid",
    confidence_suffix_high="高置信",
    confidence_suffix_medium="中置信",
    confidence_suffix_low="低置信",
    degradation_path_compare_missing_groups="path_compare 图缺少 before/after 分组节点，路径对比可能不完整",
    degradation_global_compare_missing_groups="global_compare 图缺少 before/after 分组节点，全局架构对比可能不完整",
    node_summary_label="节点摘要",
    node_risk_prefix="风险",
    node_confidence_prefix="置信",
)

_TYPE_META: tuple[DiagramTypeMeta, ...] = (
    DiagramTypeMeta(
        id="architecture",
        default_title="原项目架构 / 流程图",
        description="展示变更前（base）项目的模块层级、入口与主调用/依赖关系。",
        layout="flowchart_tb",
        agent_semantics="全局 base 架构：模块、入口、主调用链；节点 group 可用 entry/module/core。",
    ),
    DiagramTypeMeta(
        id="impact_overlay",
        default_title="PR 影响叠加图",
        description="在架构子集上标注 PR 变更波及的模块与风险等级。",
        layout="impact_subgraph",
        agent_semantics="PR 变更影响：有 risk 的节点须标注 high/medium/low；与 architecture 节点集应有差异。",
    ),
    DiagramTypeMeta(
        id="global_compare",
        default_title="全局架构前后对比图",
        description="并排对比 base 与 head 的全局模块/入口全景，突出 PR 对原架构的整体影响。",
        layout="global_compare_lr",
        agent_semantics=(
            "全局架构 before/after：从 base_index 与 head_index 提炼模块/入口；"
            "before 侧 group=before，after 侧 group=after；变更模块须填 risk；"
            "可写跨组边表示模块对应关系。与 path_compare 不同，本图覆盖全局而非关键路径。"
        ),
    ),
    DiagramTypeMeta(
        id="path_compare",
        default_title="关键路径前后对比图",
        description="关键路径在变更前后的对比；节点必须带 group=before 或 after。",
        layout="flowchart_lr",
        agent_semantics="关键路径 before/after 对比：每个节点 group 必须为 before 或 after，并填 confidence。",
    ),
)

_RISK_STYLES: dict[RiskLevel | None, StyleToken] = {
    RiskLevel.HIGH: StyleToken("riskHigh", "#fee2e2", "#dc2626", "高风险"),
    RiskLevel.MEDIUM: StyleToken("riskMed", "#fef3c7", "#d97706", "中风险"),
    RiskLevel.LOW: StyleToken("riskLow", "#dbeafe", "#2563eb", "低风险"),
    None: StyleToken("moduleDefault", "#f3f4f6", "#6b7280", "普通模块"),
}

_ENTRY_STYLE = StyleToken("entryNode", "#ecfdf5", "#059669", "入口")
_GLOBAL_BEFORE_STYLE = StyleToken("globalBefore", "#f8fafc", "#64748b", "变更前架构")
_GLOBAL_AFTER_STYLE = StyleToken("globalAfter", "#eff6ff", "#3b82f6", "变更后架构")

_CONFIDENCE_SUFFIX: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.HIGH: _UI.confidence_suffix_high,
    ConfidenceLevel.MEDIUM: _UI.confidence_suffix_medium,
    ConfidenceLevel.LOW: _UI.confidence_suffix_low,
}

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

MAX_ARCHITECTURE_NODES = 40
MAX_ARCHITECTURE_EDGES = 60
MAX_IMPACT_NODES = 40
MAX_IMPACT_EDGES = 60
MAX_GLOBAL_NODES_PER_GROUP = 20
MAX_GLOBAL_EDGES = 30
MAX_PATH_NODES_PER_GROUP = 15
MAX_PATH_EDGES = 20

OVERVIEW_RISK_PREVIEW_COUNT = 5


def get_ui_strings() -> UiStrings:
    return _UI


def get_type_meta(diagram_type: str) -> DiagramTypeMeta | None:
    for meta in _TYPE_META:
        if meta.id == diagram_type:
            return meta
    return None


def get_default_title(diagram_type: str) -> str:
    meta = get_type_meta(diagram_type)
    return meta.default_title if meta else diagram_type


def resolve_diagram_title(diagram: DiagramData) -> str:
    if diagram.title.strip():
        return diagram.title.strip()
    return get_default_title(diagram.diagram_type)


def get_risk_style(risk: RiskLevel | None) -> StyleToken:
    return _RISK_STYLES.get(risk, _RISK_STYLES[None])


def get_entry_style() -> StyleToken:
    return _ENTRY_STYLE


def get_global_before_style() -> StyleToken:
    return _GLOBAL_BEFORE_STYLE


def get_global_after_style() -> StyleToken:
    return _GLOBAL_AFTER_STYLE


def get_confidence_suffix(confidence: ConfidenceLevel | None) -> str:
    if confidence is None:
        return ""
    return _CONFIDENCE_SUFFIX.get(confidence, "")


def build_class_defs() -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for token in (
        *_RISK_STYLES.values(),
        _ENTRY_STYLE,
        _GLOBAL_BEFORE_STYLE,
        _GLOBAL_AFTER_STYLE,
    ):
        if token.class_name in seen:
            continue
        seen.add(token.class_name)
        lines.append(f"classDef {token.class_name} fill:{token.fill},stroke:{token.stroke}")
    return lines


def build_default_legend() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for risk in (RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW):
        token = _RISK_STYLES[risk]
        items.append({"key": token.class_name, "label": token.label, "color": token.fill})
    for token in (_ENTRY_STYLE, _GLOBAL_BEFORE_STYLE, _GLOBAL_AFTER_STYLE):
        items.append({"key": token.class_name, "label": token.label, "color": token.fill})
    return items


def build_agent5_instruction() -> str:
    type_lines = []
    for meta in _TYPE_META:
        type_lines.append(f"- {meta.id}: {meta.agent_semantics}")
    types_joined = "、".join(t.id for t in _TYPE_META)
    count = len(_TYPE_META)
    return (
        "输出 VisualizationSchema：summary、summary_bullets、detected_project_type、detected_framework，"
        f"以及 diagrams 恰好 {count} 张，diagram_type 必须为 {types_joined} 各一张。"
        "每张图须含 title、caption、nodes/edges；节点尽量含 confidence 与 risk（如适用）。不要输出 mermaid。\n"
        f"{count} 图语义边界：\n" + "\n".join(type_lines)
    )


def list_diagram_meta() -> dict:
    return {
        "section_label": _UI.section_label,
        "section_preview_label": _UI.section_preview_label,
        "empty_diagrams": _UI.empty_diagrams,
        "diagram_count": len(_TYPE_META),
        "overview_risk_preview_count": OVERVIEW_RISK_PREVIEW_COUNT,
        "ui_strings": {
            "render_error_title": _UI.render_error_title,
            "render_error_hint": _UI.render_error_hint,
            "unnamed_node": _UI.unnamed_node,
            "empty_structure": _UI.empty_structure,
            "node_summary_label": _UI.node_summary_label,
            "node_risk_prefix": _UI.node_risk_prefix,
            "node_confidence_prefix": _UI.node_confidence_prefix,
        },
        "default_legend": build_default_legend(),
        "diagram_types": [
            {
                "id": meta.id,
                "default_title": meta.default_title,
                "description": meta.description,
                "layout": meta.layout,
            }
            for meta in _TYPE_META
        ],
    }
