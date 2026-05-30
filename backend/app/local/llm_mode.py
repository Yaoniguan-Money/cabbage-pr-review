"""推理模式档位：Operational 参数与对外文案（单一数据源，无业务硬编码）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

LlmMode = Literal["cloud_only", "hybrid", "local_only"]

VALID_LLM_MODES: frozenset[str] = frozenset({"cloud_only", "hybrid", "local_only"})

# 503/400 错误文案单源（guard、validate、llm_helpers 均引用，禁止在业务处拼接）
HINT_CLOUD_UNAVAILABLE = (
    "当前未配置云端 API，请在 .env 设置 CLOUD_API_KEY 或 DEEPSEEK_API_KEY"
)
HINT_LOCAL_UNAVAILABLE = "本地 Ollama 不可用，请启动服务并确认 LOCAL_LLM_BASE_URL"
HINT_HYBRID_LOCAL_FOR_COMPRESS = (
    "本地 Ollama 不可用，请启动 Ollama、关闭压缩或改用纯云端"
)
HINT_COMPRESS_MODEL_REQUIRED = "混合模式启用压缩时需选择本地模型"
HINT_LOCAL_MODEL_REQUIRED = "纯本地模式需选择本地模型"
HINT_LOCAL_ONLY_BACKEND = "纯本地模式需要可用的 Ollama 与本地模型"


@dataclass(frozen=True)
class CompressToggleMeta:
    default_enabled: bool
    label: str
    hint_off: str


@dataclass(frozen=True)
class LlmModeOption:
    id: LlmMode
    label: str
    summary: str
    detail_bullets: tuple[str, ...]
    requires_cloud: bool
    requires_local: bool
    quality_warning: bool
    default: bool
    compress_toggle: CompressToggleMeta | None = None


_OPTIONS: tuple[LlmModeOption, ...] = (
    LlmModeOption(
        id="cloud_only",
        label="纯云端",
        summary="审阅结论全部由云端生成，质量与现网一致。",
        detail_bullets=(
            "Flash / Pro 均走 OpenAI 兼容云端 API",
            "不依赖本机 Ollama",
            "推荐作为默认选项",
        ),
        requires_cloud=True,
        requires_local=False,
        quality_warning=False,
        default=True,
    ),
    LlmModeOption(
        id="hybrid",
        label="混合",
        summary="云端审阅 + 本地压缩输入以节省 Token。",
        detail_bullets=(
            "Agent 结论仍由云端 Flash / Pro 生成",
            "可选本地 Ollama 压缩代码上下文",
            "关闭压缩时与纯云端行为相同",
        ),
        requires_cloud=True,
        requires_local=True,
        quality_warning=False,
        default=False,
        compress_toggle=CompressToggleMeta(
            default_enabled=True,
            label="启用本地输入压缩",
            hint_off="关闭后与纯云端行为相同，本地不参与分析",
        ),
    ),
    LlmModeOption(
        id="local_only",
        label="纯本地",
        summary="全程使用所选本地模型，质量取决于模型能力。",
        detail_bullets=(
            "Flash / Pro 档均走本机 Ollama",
            "不要求云端 API Key",
            "审阅质量因模型而异，请谨慎用于重要 PR",
        ),
        requires_cloud=False,
        requires_local=True,
        quality_warning=True,
        default=False,
    ),
)


def normalize_llm_mode(mode: str | None, fallback: str = "cloud_only") -> LlmMode:
    if mode and mode in VALID_LLM_MODES:
        return mode  # type: ignore[return-value]
    if fallback in VALID_LLM_MODES:
        return fallback  # type: ignore[return-value]
    return "cloud_only"


def get_llm_mode_option(mode: str | None, fallback: str = "cloud_only") -> LlmModeOption:
    key = normalize_llm_mode(mode, fallback)
    for opt in _OPTIONS:
        if opt.id == key:
            return opt
    return _OPTIONS[0]


def format_llm_mode_label(
    mode: str | None,
    *,
    local_compress_enabled: bool = False,
    local_model: str = "",
    fallback: str = "cloud_only",
) -> str:
    opt = get_llm_mode_option(mode, fallback)
    if opt.id == "hybrid":
        compress_part = "本地压缩已开启" if local_compress_enabled else "本地压缩已关闭"
        model_part = f" · {local_model}" if local_model.strip() else ""
        return f"{opt.label}（{compress_part}）{model_part}".strip()
    if opt.id == "local_only" and local_model.strip():
        return f"{opt.label} · {local_model.strip()}"
    return opt.label


def list_llm_mode_options(
    *,
    default_mode: str = "cloud_only",
    default_compress_enabled: bool = True,
    cloud_available: bool = False,
    local_available: bool = False,
    local_models: list[str] | None = None,
    default_local_model: str = "",
) -> dict[str, Any]:
    norm_default = normalize_llm_mode(default_mode)
    options: list[dict[str, Any]] = []
    for opt in _OPTIONS:
        item: dict[str, Any] = {
            "id": opt.id,
            "label": opt.label,
            "summary": opt.summary,
            "detail_bullets": list(opt.detail_bullets),
            "requires_cloud": opt.requires_cloud,
            "requires_local": opt.requires_local,
            "quality_warning": opt.quality_warning,
            "default": opt.id == norm_default,
            "available": _mode_available(opt.id, cloud_available, local_available),
        }
        if opt.compress_toggle is not None:
            item["compress_toggle"] = {
                "default_enabled": default_compress_enabled,
                "label": opt.compress_toggle.label,
                "hint_off": opt.compress_toggle.hint_off,
            }
        options.append(item)
    return {
        "options": options,
        "default_llm_mode": norm_default,
        "default_local_compress_enabled": default_compress_enabled,
        "cloud_available": cloud_available,
        "local_available": local_available,
        "local_models": list(local_models or []),
        "default_local_model": default_local_model,
    }


def _mode_available(mode_id: str, cloud_available: bool, local_available: bool) -> bool:
    if mode_id == "cloud_only":
        return cloud_available
    if mode_id == "hybrid":
        return cloud_available and local_available
    if mode_id == "local_only":
        return local_available
    return False


def validate_task_llm_config(
    *,
    llm_mode: str,
    local_compress_enabled: bool,
    local_model: str | None,
    cloud_available: bool,
    local_available: bool,
) -> str | None:
    """返回 None 表示合法，否则为错误说明。"""
    mode = normalize_llm_mode(llm_mode)
    opt = get_llm_mode_option(mode)
    if opt.requires_cloud and not cloud_available:
        return HINT_CLOUD_UNAVAILABLE
    if mode == "hybrid":
        if local_compress_enabled:
            if not local_available:
                return HINT_HYBRID_LOCAL_FOR_COMPRESS
            if not (local_model or "").strip():
                return HINT_COMPRESS_MODEL_REQUIRED
        return None
    if mode == "local_only":
        if not local_available:
            return HINT_LOCAL_UNAVAILABLE
        if not (local_model or "").strip():
            return HINT_LOCAL_MODEL_REQUIRED
    return None
