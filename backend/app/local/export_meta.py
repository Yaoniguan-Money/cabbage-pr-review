"""Markdown 导出下载文案与文件名单源（禁止在路由/前端硬编码）。"""

from __future__ import annotations

EXPORT_FILENAME_TEMPLATE = "pr-review-{task_id}.md"
EXPORT_DISABLED_HINT = "任务完成后可导出 Markdown 报告"
EXPORT_NOT_READY_DETAIL = "任务尚无结果可导出"
EXPORT_TASK_NOT_FOUND_DETAIL = "任务不存在"
EXPORT_META_MISSING = "无法加载导出配置，请刷新页面后重试"
EXPORT_NO_RESULT = EXPORT_NOT_READY_DETAIL
EXPORT_EMPTY_BLOB = "导出文件为空，请稍后重试"
EXPORT_LOADING = "导出中…"
EXPORT_BLOB_REVOKE_DELAY_MS = 100


def format_export_filename(task_id: str) -> str:
    return EXPORT_FILENAME_TEMPLATE.replace("{task_id}", task_id)
