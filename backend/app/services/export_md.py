from __future__ import annotations

from app.local.diagram_meta import get_ui_strings, resolve_diagram_title
from app.local.llm_mode import is_rules_only_mode
from app.local.rule_meta import RULES_MODE_NOTE
from app.models.schemas import TaskRecord, TaskResultSchema

_UI = get_ui_strings()


def export_markdown(record: TaskRecord) -> str:
    result: TaskResultSchema | None = record.result
    lines = [
        "# AI PR Review 报告",
        "",
        f"- 任务 ID: `{record.id}`",
        f"- 输入类型: {record.input_type.value}",
        f"- 推理模式: {record.llm_mode_label or record.llm_mode}",
        f"- 输入: {record.input_value[:200]}",
        "",
    ]
    if not result:
        lines.append("> 暂无分析结果")
        return "\n".join(lines)

    if is_rules_only_mode(record.llm_mode) and result.markdown_report.strip():
        lines.append(result.markdown_report.strip())
        lines.append("")
        return "\n".join(lines)

    lines.append("## 摘要")
    lines.append(result.summary)
    lines.append("")
    for b in result.summary_bullets:
        lines.append(f"- {b}")
    lines.append("")

    if record.token_stats and record.token_stats.display_segments:
        lines.append("## Token 用量")
        for seg in record.token_stats.display_segments:
            lines.append(
                f"- {seg.label}：prompt {seg.prompt_tokens} / completion {seg.completion_tokens} / 合计 {seg.total_tokens}"
            )
        lines.append("")

    lines.append("## 图表")
    for d in result.diagrams:
        title = resolve_diagram_title(d)
        lines.append(f"### {title}")
        if d.caption.strip():
            lines.append(d.caption.strip())
            lines.append("")
        lines.append("```mermaid")
        lines.append(d.mermaid or _UI.empty_export)
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
    if is_rules_only_mode(record.llm_mode):
        lines.append(f"- {RULES_MODE_NOTE}")
    lines.append("")
    return "\n".join(lines)
