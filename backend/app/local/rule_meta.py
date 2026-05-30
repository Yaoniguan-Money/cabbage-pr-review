"""规则模式 UI / Markdown 报告文案单源（禁止在业务模块硬编码）。"""

from __future__ import annotations

from typing import Any

RULES_PACK_VERSION = "1.0.0"

SECTION_SUMMARY = "摘要"
SECTION_CHANGES = "变更概览"
SECTION_RULE_HITS = "规则命中"
SECTION_RISKS = "风险列表"
SECTION_COVERAGE = "覆盖与限制"
SECTION_MISSING = "缺失信息"

NAV_REPORT = "规则报告"
NAV_OVERVIEW = "总览（默认）"
NAV_SUMMARY = "摘要"
NAV_RISKS = "风险列表"
NAV_MISSING = "缺失信息"

EMPTY_CHANGES = "未解析到变更原子。"
EMPTY_RULE_HITS = "无规则命中。"
EMPTY_RISKS = "无风险项。"
EMPTY_MISSING = "无"
RERUN_DISABLED_HINT = "纯规则模式不支持补上下文重跑。"
RULES_MODE_NOTE = "本报告由本地 YAML 规则引擎生成，不含 LLM 推理与 Mermaid 架构图。"

BACK_LINK = "← 返回输入"
EXPORT_MARKDOWN = "导出 Markdown"
INVALID_TASK = "无效任务"
TASK_FAILED_FALLBACK = "任务失败"
LOAD_FAILED = "加载失败"
RUNNING_MESSAGE = "分析进行中，请稍候…"
OVERVIEW_RISKS_PREVIEW_TITLE = "风险列表（前 {count} 条）"
DEGRADATION_BANNER = "本次分析包含降级项，请优先查看「缺失信息」确认结果可靠性。"
NO_RISKS_BUT_ATOMS_BANNER = (
    "当前未提取到风险项，但存在差异原子，可能是审阅结构化输出降级。"
    "建议查看「缺失信息」或发起一次重跑。"
)
MISSING_SECTION_TITLE = "缺失信息 / 受限条件"

TABLE_CHANGE_HEADERS = ("文件", "符号", "类型", "摘要")
TABLE_HIT_HEADERS = ("规则 ID", "严重级别", "文件", "证据摘要")


def get_ui_strings() -> dict[str, str]:
    return {
        "section_summary": SECTION_SUMMARY,
        "section_changes": SECTION_CHANGES,
        "section_rule_hits": SECTION_RULE_HITS,
        "section_risks": SECTION_RISKS,
        "section_coverage": SECTION_COVERAGE,
        "section_missing": SECTION_MISSING,
        "nav_report": NAV_REPORT,
        "nav_overview": NAV_OVERVIEW,
        "nav_summary": NAV_SUMMARY,
        "nav_risks": NAV_RISKS,
        "nav_missing": NAV_MISSING,
        "empty_changes": EMPTY_CHANGES,
        "empty_rule_hits": EMPTY_RULE_HITS,
        "empty_risks": EMPTY_RISKS,
        "empty_missing": EMPTY_MISSING,
        "rerun_disabled_hint": RERUN_DISABLED_HINT,
        "rules_mode_note": RULES_MODE_NOTE,
        "back_link": BACK_LINK,
        "export_markdown": EXPORT_MARKDOWN,
        "invalid_task": INVALID_TASK,
        "task_failed_fallback": TASK_FAILED_FALLBACK,
        "load_failed": LOAD_FAILED,
        "running_message": RUNNING_MESSAGE,
        "degradation_banner": DEGRADATION_BANNER,
        "no_risks_but_atoms_banner": NO_RISKS_BUT_ATOMS_BANNER,
        "missing_section_title": MISSING_SECTION_TITLE,
    }


def format_overview_risks_preview_title(count: int) -> str:
    return OVERVIEW_RISKS_PREVIEW_TITLE.format(count=count)


def list_rules_meta(*, overview_risk_preview_count: int = 5) -> dict[str, Any]:
    ui = get_ui_strings()
    ui["overview_risks_preview_title"] = format_overview_risks_preview_title(overview_risk_preview_count)
    return {
        "rules_pack_version": RULES_PACK_VERSION,
        "visualization_mode": "markdown",
        "ui_strings": ui,
        "table_change_headers": list(TABLE_CHANGE_HEADERS),
        "table_hit_headers": list(TABLE_HIT_HEADERS),
    }
