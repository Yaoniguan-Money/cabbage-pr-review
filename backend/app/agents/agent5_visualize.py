from __future__ import annotations

from app.local.mermaid_render import render_diagram
from app.local.project_detect import detect_project
from app.models.schemas import (
    DiagramData,
    DiffCompareSchema,
    GraphEdge,
    GraphNode,
    ProjectIndexSchema,
    RiskReviewSchema,
    TaskResultSchema,
    VisualizationSchema,
)


def _build_path_compare(base: ProjectIndexSchema, head: ProjectIndexSchema, diff: DiffCompareSchema) -> DiagramData:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    key_paths = (base.flow_hints + head.flow_hints)[:6] or ["主流程"]
    for i, hint in enumerate(key_paths[:4]):
        nodes.append(GraphNode(id=f"b{i}", label=hint[:40], group="before"))
    for i, hint in enumerate(key_paths[:4]):
        nodes.append(GraphNode(id=f"a{i}", label=hint[:40] + " (PR)", group="after"))
    for i in range(min(len(key_paths), 4)):
        edges.append(GraphEdge(source=f"b{i}", target=f"a{i}", label="变更"))
    if diff.all_atoms:
        atom = diff.all_atoms[0]
        nodes.append(GraphNode(id="risk0", label=atom.file_path[:40], group="after", risk=None))
    diagram = DiagramData(diagram_type="path_compare", nodes=nodes, edges=edges)
    diagram.mermaid = render_diagram(diagram)
    return diagram


def run_agent5(
    base: ProjectIndexSchema,
    head: ProjectIndexSchema,
    diff: DiffCompareSchema,
    review: RiskReviewSchema,
    pr_context: dict,
    project_type: str | None,
    framework: str | None,
) -> TaskResultSchema:
    detected_pt, detected_fw = detect_project(pr_context.get("file_paths", []), pr_context.get("patches"))
    pt = project_type or detected_pt
    fw = framework or detected_fw
    diagrams: list[DiagramData] = []
    if base.architecture_diagram:
        diagrams.append(base.architecture_diagram)
    elif base.modules:
        from app.local.mermaid_render import diagram_from_modules

        d = diagram_from_modules("architecture", base.modules, base.routes)
        d.mermaid = render_diagram(d)
        diagrams.append(d)
    if diff.impact_diagram:
        diagrams.append(diff.impact_diagram)
    path_cmp = _build_path_compare(base, head, diff)
    diagrams.append(path_cmp)
    from app.models.schemas import RiskLevel

    high_risks = [r for r in review.risks if r.risk_level == RiskLevel.HIGH]
    bullets = [
        f"PR：{pr_context.get('title', '未命名')[:60]}",
        f"变更文件：{pr_context.get('changed_files_count', len(pr_context.get('file_paths', [])))} 个",
        f"识别框架：{fw}（{pt}）",
        f"风险项：{len(review.risks)} 条（高：{len(high_risks)}）",
    ]
    summary = f"本次 PR 共影响 {len(diff.all_atoms)} 个差异原子，建议优先关注 {len(high_risks)} 项高风险。"
    return TaskResultSchema(
        summary=summary,
        summary_bullets=bullets,
        diagrams=diagrams,
        risks=review.risks,
        missing_info=review.missing_info,
        degradation_notes=review.degradation_notes,
        diff_atoms=diff.all_atoms,
        base_index=base,
        head_index=head,
        detected_project_type=pt,
        detected_framework=fw,
    )
