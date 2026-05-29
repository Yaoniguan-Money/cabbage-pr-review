"""已弃用：项目类型/框架仅由 Agent5 LLM 的 detected_* 字段提供，主链路不得调用本模块。"""

from __future__ import annotations

from typing import Any


def detect_project(file_paths: list[str], patches: list[dict] | None = None) -> tuple[str, str]:
    raise NotImplementedError("project_detect 已弃用，请使用 Agent5 VisualizationSchema.detected_*")
