"""云端厂商预设（无密钥，仅 base URL 与模型名建议）。"""

from __future__ import annotations

from typing import Any


def list_provider_presets() -> dict[str, Any]:
    return {
        "presets": [
            {
                "id": "deepseek",
                "label": "DeepSeek",
                "api_base": "https://api.deepseek.com",
                "flash_model": "deepseek-v4-flash",
                "pro_model": "deepseek-v4-pro",
            },
            {
                "id": "openai",
                "label": "OpenAI",
                "api_base": "https://api.openai.com/v1",
                "flash_model": "gpt-4o-mini",
                "pro_model": "gpt-4o",
            },
            {
                "id": "custom",
                "label": "自定义兼容接口",
                "api_base": "",
                "flash_model": "",
                "pro_model": "",
            },
        ],
    }
