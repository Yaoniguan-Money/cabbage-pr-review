"""前端 API 客户端错误文案单源。"""

from __future__ import annotations

from typing import Any

from app.config import settings

MOCK_MODE_BANNER = (
    "当前为 Mock LLM 演示模式：审阅结论由占位逻辑生成，不代表真实规则引擎质量。"
    "规则引擎主路径请使用 docker-compose.demo.yml（rules_only）。"
)

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
    "fetch_demo_patches": "无法加载演示 Patch 场景",
    "fetch_rules_catalog": "无法加载规则目录",
}


def get_error_messages() -> dict[str, str]:
    return dict(_ERROR_MESSAGES)


def list_client_meta() -> dict[str, Any]:
    return {
        "error_messages": get_error_messages(),
        "use_mock_llm": settings.use_mock_llm,
        "mock_mode_banner": MOCK_MODE_BANNER,
    }
