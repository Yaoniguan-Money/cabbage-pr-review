"""输入页 UI 文案与选项单源（禁止在前端硬编码）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.schemas import InputType


@dataclass(frozen=True)
class SelectOption:
    id: str
    label: str


@dataclass(frozen=True)
class InputTabMeta:
    id: InputType
    title: str
    hint: str


_PROJECT_TYPES: tuple[SelectOption, ...] = (
    SelectOption("python-api", "python-api"),
    SelectOption("node-api", "node-api"),
    SelectOption("frontend", "frontend"),
    SelectOption("python", "python"),
    SelectOption("typescript", "typescript"),
    SelectOption("unknown", "unknown"),
)

_FRAMEWORKS: tuple[SelectOption, ...] = (
    SelectOption("FastAPI", "FastAPI"),
    SelectOption("Express", "Express"),
    SelectOption("React/Vite", "React/Vite"),
    SelectOption("Python", "Python"),
    SelectOption("TypeScript/JavaScript", "TypeScript/JavaScript"),
    SelectOption("unknown", "unknown"),
)

_TABS: tuple[InputTabMeta, ...] = (
    InputTabMeta("pr_url", "PR URL", "https://github.com/owner/repo/pull/123"),
    InputTabMeta("patch", "Patch / Diff", "粘贴 diff 或 patch 文本"),
    InputTabMeta("local_path", "本地仓库路径", "例如 C:\\projects\\my-app"),
)

_UI_STRINGS: dict[str, str] = {
    "llm_mode_label": "推理模式（任务开始前选择，运行中不可改）",
    "local_model_label": "本地模型（Ollama）",
    "local_model_placeholder": "输入本机 Ollama 已安装的模型名",
    "review_depth_label": "审阅深度（任务开始前选择，运行中不可改）",
    "input_content_label": "输入内容",
    "patch_placeholder": "diff --git ...",
    "project_type_label": "项目类型（可手动确认）",
    "framework_label": "框架（可手动切换）",
    "submit_loading": "创建任务中…",
    "submit_idle": "开始分析",
    "examples_heading": "官方示例 PR（一键填充）",
    "error_load_review_depth": "无法加载审阅深度选项",
    "error_load_llm_mode": "无法加载推理模式选项",
    "error_submit": "提交失败",
}


def list_input_page_meta() -> dict[str, Any]:
    return {
        "default_project_type": "unknown",
        "default_framework": "unknown",
        "project_types": [{"id": o.id, "label": o.label} for o in _PROJECT_TYPES],
        "frameworks": [{"id": o.id, "label": o.label} for o in _FRAMEWORKS],
        "input_tabs": [{"id": t.id, "title": t.title, "hint": t.hint} for t in _TABS],
        "ui_strings": dict(_UI_STRINGS),
    }
