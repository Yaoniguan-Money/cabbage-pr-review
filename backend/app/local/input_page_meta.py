"""输入页 UI 文案与选项单源（禁止在前端硬编码）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.local.detail_page_meta import APP_NAME, APP_TAGLINE
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
)

_USAGE_GUIDE: dict[str, Any] = {
    "title": "使用说明",
    "toggle_show": "展开使用说明",
    "toggle_hide": "收起使用说明",
    "default_expanded": True,
    "sections": [
        {
            "id": "security_and_demo",
            "heading": "安全与评委演示",
            "paragraphs": [
                "本演示站不会在服务器上保存管理员的 API Key 或 GitHub Token。",
                "您在下方填写并「保存到本机」的内容，只存在您的浏览器，仅在您点击「开始分析」时用于这一次任务，不会写入服务器硬盘。",
                "其他访问者无法使用您保存在自己电脑浏览器里的凭据。",
                "评委建议：在「评委演示 Patch」中任选场景并加载 → 推理模式选择「纯规则」→ 点击「开始分析」，即可完整体验规则引擎、差异分析与报告结构，无需 API Key、无需 GitHub Token。",
            ],
        },
        {
            "id": "llm_optional",
            "heading": "完整 LLM 审阅（可选）",
            "paragraphs": [
                "若需大模型审阅（非纯规则）：请打开「启用云端 LLM API」，填写 API Key 与模型名称，并点击「保存到本机」；或在本机安装 Ollama 后，选择支持本地模型的推理模式。以上配置仅对您当前浏览器生效，不会影响其他访问者。",
            ],
        },
        {
            "id": "pr_optional",
            "heading": "分析 GitHub PR 链接（可选）",
            "paragraphs": [
                "若需输入 PR URL 并从 GitHub 拉取变更：请打开「启用 GitHub Token」，填写具有仓库读权限的 Token，并「保存到本机」。未配置时仅适合公开仓库，且可能因 GitHub 限速或网络波动导致拉取失败；关闭开关则本次任务不使用您浏览器中已保存的 Token。",
            ],
        },
    ],
}

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
    "demo_patches_heading": "评委演示 Patch（一键加载）",
    "demo_patches_hint": "加载后请确认推理模式为「纯规则」，再点击开始分析",
    "demo_step_select": "1. 选择演示 Patch",
    "demo_step_mode": "2. 确认纯规则模式",
    "demo_step_run": "3. 开始分析",
    "error_load_demo_patches": "无法加载评委演示 Patch，请确认 data/demo 已挂载或使用 docker-compose.demo.yml",
    "rules_catalog_heading": "规则包目录（只读）",
    "rules_catalog_toggle_show": "展开规则列表",
    "rules_catalog_toggle_hide": "收起规则列表",
    "rules_catalog_count_label": "共 {count} 条规则",
    "rules_catalog_invalid_label": "校验问题 {count} 条",
    "rules_catalog_version_label": "规则包版本 {version}",
    "demo_scenario_load": "加载场景",
    "demo_scenario_expected": "预期命中",
    "error_load_review_depth": "无法加载审阅深度选项",
    "error_load_llm_mode": "无法加载推理模式选项",
    "error_submit": "提交失败",
    "error_pr_github_required": (
        "公网演示站不会在服务器使用管理员的 GitHub Token。"
        "请改用「评委演示 Patch」，或在下方启用 GitHub Token 并保存到本机后再分析 PR。"
    ),
    "credentials_warm_tips_title": "温馨提示",
    "credentials_warm_tips_body": (
        "若希望发挥全部性能，可配置 LLM API、使用本机大模型，或配置 GitHub Token 以稳定拉取 PR。"
    ),
}


def list_input_page_meta() -> dict[str, Any]:
    return {
        "app_name": APP_NAME,
        "app_tagline": APP_TAGLINE,
        "default_project_type": "unknown",
        "default_framework": "unknown",
        "project_types": [{"id": o.id, "label": o.label} for o in _PROJECT_TYPES],
        "frameworks": [{"id": o.id, "label": o.label} for o in _FRAMEWORKS],
        "input_tabs": [{"id": t.id, "title": t.title, "hint": t.hint} for t in _TABS],
        "ui_strings": dict(_UI_STRINGS),
        "usage_guide": dict(_USAGE_GUIDE),
        "is_public_deploy": settings.is_public_deploy,
    }
