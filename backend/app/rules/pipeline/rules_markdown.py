"""规则模式：Markdown 报告生成。"""

from __future__ import annotations

from app.local.rule_meta import TABLE_CHANGE_HEADERS, TABLE_HIT_HEADERS, get_ui_strings
from app.models.schemas import DiffCompareSchema, ProjectIndexSchema, RiskReviewSchema, TaskResultSchema
from app.rules.rule_schema import RuleHitRecord


def _escape_cell(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def build_markdown_report(
    *,
    summary_line: str,
    diff: DiffCompareSchema,
    review: RiskReviewSchema,
    hits: list[RuleHitRecord],
    extra_notes: list[str] | None = None,
    base_index: ProjectIndexSchema | None = None,
    head_index: ProjectIndexSchema | None = None,
) -> str:
    ui = get_ui_strings()
    lines: list[str] = [
        f"## {ui['section_summary']}",
        "",
        summary_line,
        "",
        f"## {ui['section_changes']}",
        "",
    ]

    if diff.all_atoms:
        headers = list(TABLE_CHANGE_HEADERS)
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for atom in diff.all_atoms[:100]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_cell(atom.file_path),
                        _escape_cell(atom.symbol or "—"),
                        _escape_cell(atom.change_type),
                        _escape_cell(atom.summary),
                    ]
                )
                + " |"
            )
    else:
        lines.append(ui["empty_changes"])

    if base_index or head_index:
        lines.extend(["", f"## {ui['section_index']}", ""])
        if base_index and base_index.entry_files:
            lines.append(f"- base 入口：{', '.join(base_index.entry_files[:10])}")
        if head_index and head_index.entry_files:
            lines.append(f"- head 入口：{', '.join(head_index.entry_files[:10])}")
        if base_index and base_index.modules:
            lines.append(f"- base 顶层模块：{', '.join(base_index.modules[:10])}")
        if head_index and head_index.modules:
            lines.append(f"- head 顶层模块：{', '.join(head_index.modules[:10])}")

    lines.extend(["", f"## {ui['section_rule_hits']}", ""])
    if hits:
        hit_headers = list(TABLE_HIT_HEADERS)
        lines.append("| " + " | ".join(hit_headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(hit_headers)) + " |")
        for hit in hits[:100]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_cell(hit.rule_id),
                        _escape_cell(hit.severity),
                        _escape_cell(hit.file_path),
                        _escape_cell(hit.evidence[:200]),
                    ]
                )
                + " |"
            )
    else:
        lines.append(ui["empty_rule_hits"])

    lines.extend(["", f"## {ui['section_risks']}", ""])
    if review.risks:
        for risk in review.risks:
            lines.append(
                f"- **[{risk.risk_level.value.upper()}]** {_escape_cell(risk.title)}"
            )
            if risk.evidence:
                lines.append(f"  - 证据: {_escape_cell(risk.evidence[:400])}")
            if risk.suggestion:
                lines.append(f"  - 建议: {_escape_cell(risk.suggestion)}")
    else:
        lines.append(ui["empty_risks"])

    lines.extend(["", f"## {ui['section_coverage']}", ""])
    lines.append(ui["rules_mode_note"])
    all_notes = list(review.degradation_notes) + list(extra_notes or [])
    for note in all_notes:
        lines.append(f"- {note}")

    return "\n".join(lines)


def build_summary_from_hits(
    diff: DiffCompareSchema,
    hits: list[RuleHitRecord],
    risks_count: int,
) -> tuple[str, list[str]]:
    line = (
        f"共解析 {len(diff.all_atoms)} 个变更原子，"
        f"规则命中 {len(hits)} 次，生成 {risks_count} 条风险。"
    )
    bullets = [
        f"变更文件/原子：{len(diff.all_atoms)}",
        f"规则命中：{len(hits)}",
        f"风险条目：{risks_count}",
    ]
    return line, bullets


def run_rules_finalize(
    *,
    diff: DiffCompareSchema,
    review: RiskReviewSchema,
    hits: list[RuleHitRecord],
    review_stats,
    project_type: str | None,
    framework: str | None,
    extra_notes: list[str] | None = None,
    base_index: ProjectIndexSchema | None = None,
    head_index: ProjectIndexSchema | None = None,
) -> TaskResultSchema:
    summary, bullets = build_summary_from_hits(diff, hits, len(review.risks))
    markdown = build_markdown_report(
        summary_line=summary,
        diff=diff,
        review=review,
        hits=hits,
        extra_notes=extra_notes,
        base_index=base_index,
        head_index=head_index,
    )
    return TaskResultSchema(
        summary=summary,
        summary_bullets=bullets,
        diagrams=[],
        risks=review.risks,
        missing_info=review.missing_info,
        degradation_notes=list(review.degradation_notes) + list(extra_notes or []),
        diff_atoms=diff.all_atoms,
        base_index=base_index,
        head_index=head_index,
        detected_project_type=project_type or "",
        detected_framework=framework or "",
        review_stats=review_stats,
        markdown_report=markdown,
        rule_hits=hits,
    )
