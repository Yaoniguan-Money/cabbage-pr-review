"""详情页三栏布局文案单源（禁止在前端硬编码）。"""

from __future__ import annotations

from typing import Any

from app.local.export_meta import (
    EXPORT_BLOB_REVOKE_DELAY_MS,
    EXPORT_DISABLED_HINT,
    EXPORT_EMPTY_BLOB,
    EXPORT_FILENAME_TEMPLATE,
    EXPORT_LOADING,
    EXPORT_META_MISSING,
    EXPORT_NO_RESULT,
)

NAV_FILES = "变更文件"
APP_NAME = "AI PR Review 助手"
APP_TAGLINE = "结构化影响分析与审阅辅助（定稿 v2.0）"

STATUS_PENDING = "等待中"
STATUS_RUNNING = "分析中"
STATUS_COMPLETED = "已完成"
STATUS_FAILED = "失败"

TASK_ID_LABEL = "任务 ID"
TASK_ID_TOGGLE_SHOW = "显示任务 ID"
TASK_ID_TOGGLE_HIDE = "隐藏任务 ID"
AGENT_STEPPER_LABEL = "分析进度"
AGENT_PARALLEL_LANE_ARIA = "并行扫描步骤"
PARALLEL_RUNNING_HINT = "正在并行扫描原版本与 PR 版本…"
ALERT_DEGRADATION_TITLE = "分析降级提示"
BRANCH_INTO = "into {ref}"
META_LLM_MODE = "推理模式"
META_REVIEW_DEPTH = "审阅深度"
META_ATOMS_SCANNED = "已扫描 {reviewed}/{total} 个差异点"
META_LLM_CALLS = "Pro ×{pro} · Flash ×{flash}"
META_COMPRESS = "本地压缩 {calls} 次（{before}→{after} 字符）"
META_TOKEN_SEGMENT = "{label} {total}"

FILES_SIDEBAR_LABEL = "变更文件"
DIFF_EMPTY = "该文件暂无 patch 文本"
DIFF_SELECT_HINT = "选择左侧文件查看 diff"
NO_FILES = "暂无变更文件"
OPEN_PR_LINK = "在 GitHub 打开"

AI_PANEL_TITLE = "AI 审阅摘要"
OVERALL_RISK_LABEL = "整体风险"
RISK_LEVEL_NONE = "无"
RISK_LEVEL_HIGH = "高"
RISK_LEVEL_MEDIUM = "中"
RISK_LEVEL_LOW = "低"
SUGGESTED_FINDINGS_LABEL = "关键发现"
VIEW_DIAGRAMS = "查看示例图"
VIEW_FULL_RISKS = "查看全部风险"

STAT_CHECKS = "变更统计"
STAT_FILES = "文件数"
STAT_ADDITIONS = "新增行"
STAT_DELETIONS = "删除行"
STAT_REVIEW_PROGRESS = "审阅进度"

SUMMARY_HEADING = "摘要"
SUMMARY_DETECTED = "识别：{framework} / {project_type}"

RERUN_TITLE = "纠偏：补上下文重跑（仅一次）"
RERUN_HINT = "勾选 1~3 个差异点作为重点复审，并可补充文件/目录路径。"
RERUN_PATHS_PLACEHOLDER = "补充上下文路径，每行一个"
RERUN_SUBMIT_LOADING = "重跑中…"
RERUN_SUBMIT_IDLE = "补上下文并重跑"
RERUN_ERROR_FALLBACK = "重跑失败"

RISK_SORT_LABEL = "排序："
RISK_SORT_BY_RISK = "按风险等级"
RISK_SORT_BY_CONFIDENCE = "按置信度"
RISK_META = "风险: {level} | 置信度: {confidence}"
RISK_EVIDENCE = "证据：{text}"
RISK_SUGGESTION = "建议：{text}"
RISK_EMPTY = "暂无风险项"

SEVERITY_FILTER_ALL = "全部"
META_LOADING = "加载中…"

EXPORT_FILENAME_TEMPLATE_UI = EXPORT_FILENAME_TEMPLATE
EXPORT_DISABLED_HINT_UI = EXPORT_DISABLED_HINT
EXPORT_META_MISSING_UI = EXPORT_META_MISSING
EXPORT_NO_RESULT_UI = EXPORT_NO_RESULT
EXPORT_EMPTY_BLOB_UI = EXPORT_EMPTY_BLOB
EXPORT_LOADING_UI = EXPORT_LOADING


def get_ui_strings() -> dict[str, str]:
    return {
        "nav_files": NAV_FILES,
        "app_name": APP_NAME,
        "app_tagline": APP_TAGLINE,
        "status_pending": STATUS_PENDING,
        "status_running": STATUS_RUNNING,
        "status_completed": STATUS_COMPLETED,
        "status_failed": STATUS_FAILED,
        "task_id_label": TASK_ID_LABEL,
        "task_id_toggle_show": TASK_ID_TOGGLE_SHOW,
        "task_id_toggle_hide": TASK_ID_TOGGLE_HIDE,
        "agent_stepper_label": AGENT_STEPPER_LABEL,
        "agent_parallel_lane_aria": AGENT_PARALLEL_LANE_ARIA,
        "parallel_running_hint": PARALLEL_RUNNING_HINT,
        "alert_degradation_title": ALERT_DEGRADATION_TITLE,
        "branch_into": BRANCH_INTO,
        "meta_llm_mode": META_LLM_MODE,
        "meta_review_depth": META_REVIEW_DEPTH,
        "meta_atoms_scanned": META_ATOMS_SCANNED,
        "meta_llm_calls": META_LLM_CALLS,
        "meta_compress": META_COMPRESS,
        "meta_token_segment": META_TOKEN_SEGMENT,
        "files_sidebar_label": FILES_SIDEBAR_LABEL,
        "diff_empty": DIFF_EMPTY,
        "diff_select_hint": DIFF_SELECT_HINT,
        "no_files": NO_FILES,
        "open_pr_link": OPEN_PR_LINK,
        "ai_panel_title": AI_PANEL_TITLE,
        "overall_risk_label": OVERALL_RISK_LABEL,
        "risk_level_none": RISK_LEVEL_NONE,
        "risk_level_high": RISK_LEVEL_HIGH,
        "risk_level_medium": RISK_LEVEL_MEDIUM,
        "risk_level_low": RISK_LEVEL_LOW,
        "suggested_findings_label": SUGGESTED_FINDINGS_LABEL,
        "view_diagrams": VIEW_DIAGRAMS,
        "view_full_risks": VIEW_FULL_RISKS,
        "stat_checks": STAT_CHECKS,
        "stat_files": STAT_FILES,
        "stat_additions": STAT_ADDITIONS,
        "stat_deletions": STAT_DELETIONS,
        "stat_review_progress": STAT_REVIEW_PROGRESS,
        "summary_heading": SUMMARY_HEADING,
        "summary_detected": SUMMARY_DETECTED,
        "rerun_title": RERUN_TITLE,
        "rerun_hint": RERUN_HINT,
        "rerun_paths_placeholder": RERUN_PATHS_PLACEHOLDER,
        "rerun_submit_loading": RERUN_SUBMIT_LOADING,
        "rerun_submit_idle": RERUN_SUBMIT_IDLE,
        "rerun_error_fallback": RERUN_ERROR_FALLBACK,
        "risk_sort_label": RISK_SORT_LABEL,
        "risk_sort_by_risk": RISK_SORT_BY_RISK,
        "risk_sort_by_confidence": RISK_SORT_BY_CONFIDENCE,
        "risk_meta": RISK_META,
        "risk_evidence": RISK_EVIDENCE,
        "risk_suggestion": RISK_SUGGESTION,
        "risk_empty": RISK_EMPTY,
        "severity_filter_all": SEVERITY_FILTER_ALL,
        "meta_loading": META_LOADING,
        "export_filename_template": EXPORT_FILENAME_TEMPLATE_UI,
        "export_disabled_hint": EXPORT_DISABLED_HINT_UI,
        "export_meta_missing": EXPORT_META_MISSING_UI,
        "export_no_result": EXPORT_NO_RESULT_UI,
        "export_empty_blob": EXPORT_EMPTY_BLOB_UI,
        "export_loading": EXPORT_LOADING_UI,
    }


def list_detail_page_meta() -> dict[str, Any]:
    return {
        "ui_strings": get_ui_strings(),
        "export_blob_revoke_delay_ms": EXPORT_BLOB_REVOKE_DELAY_MS,
    }
