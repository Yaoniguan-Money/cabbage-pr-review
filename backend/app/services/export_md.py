from __future__ import annotations

from app.models.schemas import TaskRecord, TaskResultSchema

DIAGRAM_TITLES = {
    "architecture": "原项目架构 / 流程图",
    "impact_overlay": "PR 影响叠加图",
    "path_compare": "关键路径前后对比图",
}


def export_markdown(record: TaskRecord) -> str:
    result: TaskResultSchema | None = record.result
    lines = [
        f"# AI PR Review 报告",
        "",
        f"- 任务 ID: `{record.id}`",
        f"- 输入类型: {record.input_type.value}",
        f"- 输入: {record.input_value[:200]}",
        "",
    ]
    if not result:
        lines.append("> 暂无分析结果")
        return "\n".join(lines)

    lines.append("## 摘要")
    lines.append(result.summary)
    lines.append("")
    for b in result.summary_bullets:
        lines.append(f"- {b}")
    lines.append("")

    lines.append("## 图表")
    for d in result.diagrams:
        title = DIAGRAM_TITLES.get(d.diagram_type, d.diagram_type)
        lines.append(f"### {title}")
        lines.append("```mermaid")
        lines.append(d.mermaid or "flowchart TB\n  empty[暂无数据]")
        lines.append("```")
        lines.append("")

    lines.append("## 风险列表")
    if not result.risks:
        lines.append("- 无")
    for r in result.risks:
        lines.append(
            f"- **[{r.risk_level.value.upper()}]** {r.title}（置信度: {r.confidence.value}）\n  {r.description}"
        )
        if r.evidence:
            lines.append(f"  - 证据: {r.evidence[:500]}")
        if r.suggestion:
            lines.append(f"  - 建议: {r.suggestion}")
    lines.append("")

    lines.append("## 缺失信息 / 受限条件")
    if not result.missing_info and not result.degradation_notes:
        lines.append("- 无")
    for m in result.missing_info:
        lines.append(f"- **{m.module}**: {m.reason}。{m.suggestion}")
    for n in result.degradation_notes:
        lines.append(f"- {n}")
    lines.append("")
    return "\n".join(lines)
