"""运行时凭据配置 UI 文案单源。"""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.llm.credentials_resolve import server_cloud_configured, server_github_configured

# 首页引导（用户指定文案）
RUNTIME_CREDENTIALS_ONBOARDING = "如想体验最佳效果请配置您的 API Key"

_UI_STRINGS: dict[str, str] = {
    "panel_title": "API 与 GitHub 设置",
    "panel_summary": "凭据仅保存在本浏览器，随分析任务提交，不会写入服务器磁盘。",
    "onboarding_banner": RUNTIME_CREDENTIALS_ONBOARDING,
    "toggle_cloud_label": "启用云端 LLM API",
    "toggle_github_label": "启用 GitHub Token",
    "status_cloud_ready": "云端 API 已就绪，可选纯云端/混合等推理模式",
    "status_cloud_off": "未启用或未填写 API Key",
    "status_cloud_server": "服务器已配置云端 API",
    "status_cloud_public": "未启用或未填写 API Key；评委演示请用「纯规则」",
    "status_github_ready": "GitHub Token 已就绪，拉取 PR 更稳定",
    "status_github_off": "未启用或未填写 Token，公开 PR 可能受网络影响",
    "status_github_server": "服务器已配置 GitHub Token",
    "status_github_public": "未配置 Token；请用 Patch 演示，或在本机启用并保存 Token",
    "status_local_ready": "检测到本机 Ollama，可使用本地大模型",
    "status_local_off": "本机 Ollama 未就绪，可配置 API 或安装后使用本地模式",
    "preset_label": "厂商预设",
    "api_base_label": "API Base URL",
    "api_key_label": "云端 API Key",
    "flash_model_label": "Flash 模型",
    "pro_model_label": "Pro 模型",
    "github_token_label": "GitHub Token（分析 PR 时建议填写）",
    "save_local_button": "保存到本机",
    "clear_button": "清除凭据",
    "saved_hint": "已保存到本机浏览器，开始分析时将随任务提交。",
}


def list_runtime_config_meta() -> dict[str, Any]:
    return {
        "allow_runtime_credentials": settings.allow_runtime_credentials,
        "deploy_mode": settings.deploy_mode.strip().lower(),
        "is_public_deploy": settings.is_public_deploy,
        "server_cloud_configured": server_cloud_configured(),
        "server_github_configured": server_github_configured(),
        "expand_panel_default": settings.is_public_deploy,
        "ui_strings": dict(_UI_STRINGS),
    }
