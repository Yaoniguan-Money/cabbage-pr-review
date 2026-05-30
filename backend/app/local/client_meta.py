"""前端 API 客户端错误文案单源。"""

from __future__ import annotations

from typing import Any

_ERROR_MESSAGES: dict[str, str] = {
    "create_task": "创建任务失败",
    "get_task": "获取任务失败",
    "get_task_result": "结果尚未就绪",
    "rerun_task": "重跑失败",
    "fetch_review_depth": "无法加载审阅深度选项",
    "fetch_llm_mode": "无法加载推理模式选项",
    "fetch_rules_meta": "无法加载规则模式元数据",
    "fetch_diagram_meta": "无法加载图表元数据",
    "fetch_input_page_meta": "无法加载输入页元数据",
    "fetch_client_meta": "无法加载客户端元数据",
}


def get_error_messages() -> dict[str, str]:
    return dict(_ERROR_MESSAGES)


def list_client_meta() -> dict[str, Any]:
    return {"error_messages": get_error_messages()}
