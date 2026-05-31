"""推理模式档位：Operational 参数与对外文案（单一数据源，无业务硬编码）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

LlmMode = Literal["cloud_only", "hybrid", "local_only", "rules_only"]

VALID_LLM_MODES: frozenset[str] = frozenset({"cloud_only", "hybrid", "local_only", "rules_only"})

HINT_CLOUD_UNAVAILABLE_ENV = (
    "当前未配置云端 API，请在 .env 设置 CLOUD_API_KEY 或 DEEPSEEK_API_KEY"
)
HINT_CLOUD_UNAVAILABLE_BROWSER = (
    "请先打开上方「启用云端 LLM API」，填写 API Key 并点击「保存到本机」；"
    "凭据仅保存在您浏览器，不会写入服务器。"
)
# 兼容旧引用
HINT_CLOUD_UNAVAILABLE = HINT_CLOUD_UNAVAILABLE_ENV


def resolve_cloud_unavailable_hint() -> str:
    """按部署方式返回云端不可用提示（单源，供 API / 校验 / 503 共用）。"""
    from app.config import settings
    from app.llm.credentials_resolve import server_cloud_configured

    if settings.allow_runtime_credentials and not server_cloud_configured():
        return HINT_CLOUD_UNAVAILABLE_BROWSER
    return HINT_CLOUD_UNAVAILABLE_ENV
HINT_LOCAL_UNAVAILABLE = "本地 Ollama 不可用，请启动服务并确认 LOCAL_LLM_BASE_URL"
HINT_HYBRID_LOCAL_FOR_COMPRESS = (
    "本地 Ollama 不可用，请启动 Ollama、关闭压缩或改用纯云端"
)
HINT_COMPRESS_MODEL_REQUIRED = "混合模式启用压缩时需选择本地模型"
HINT_LOCAL_MODEL_REQUIRED = "纯本地模式需选择本地模型"
HINT_LOCAL_ONLY_BACKEND = "纯本地模式需要可用的 Ollama 与本地模型"
HINT_RERUN_NOT_SUPPORTED = "纯规则模式不支持补上下文重跑"


@dataclass(frozen=True)
class CompressToggleMeta:
    default_enabled: bool
    label: str
    hint_off: str


@dataclass(frozen=True)
class LlmModeOption:
    id: str
    label: str
    summary: str
    detail_bullets: tuple[str, ...]
    requires_cloud: bool
    requires_local: bool
    requires_llm: bool
    quality_warning: bool
    visualization_mode: Literal["diagrams", "markdown"]
    rerun_supported: bool
    hide_token_stats: bool
    default: bool
    local_model_required: bool = False
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
        requires_llm=True,
        quality_warning=False,
        visualization_mode="diagrams",
        rerun_supported=True,
        hide_token_stats=False,
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
        requires_llm=True,
        quality_warning=False,
        visualization_mode="diagrams",
        rerun_supported=True,
        hide_token_stats=False,
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
        requires_llm=True,
        quality_warning=True,
        visualization_mode="diagrams",
        rerun_supported=True,
        hide_token_stats=False,
        default=False,
        local_model_required=True,
    ),
    LlmModeOption(
        id="rules_only",
        label="纯规则",
        summary="零 LLM，由内置 YAML 规则引擎审阅并生成四张可视化图。",
        detail_bullets=(
            "无需 Cloud API Key 与 Ollama",
            "规则来自可配置 YAML 包，命中结果可审计",
            "输出 Markdown 报告与四张 Mermaid 架构图",
        ),
        requires_cloud=False,
        requires_local=False,
        requires_llm=False,
        quality_warning=True,
        visualization_mode="diagrams",
        rerun_supported=False,
        hide_token_stats=True,
        default=False,
    ),
)


def is_rules_only_mode(mode: str | None) -> bool:
    return normalize_llm_mode(mode) == "rules_only"


def normalize_llm_mode(mode: str | None, fallback: str = "cloud_only") -> str:
    if mode and mode in VALID_LLM_MODES:
        return mode
    if fallback in VALID_LLM_MODES:
        return fallback
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


def get_availability_hints() -> dict[str, str]:
    """前端推导运行时可用性时使用的提示文案单源。"""
    return {
        "cloud_unavailable": resolve_cloud_unavailable_hint(),
        "local_unavailable": HINT_LOCAL_UNAVAILABLE,
        "local_for_compress": HINT_HYBRID_LOCAL_FOR_COMPRESS,
        "compress_model_required": HINT_COMPRESS_MODEL_REQUIRED,
        "local_model_required": HINT_LOCAL_MODEL_REQUIRED,
    }


def needs_local_model_at_runtime(opt: LlmModeOption, compress_enabled: bool) -> bool:
    if opt.local_model_required:
        return True
    if opt.compress_toggle is not None and compress_enabled:
        return True
    return False


def needs_local_at_runtime(opt: LlmModeOption, compress_enabled: bool) -> bool:
    if not opt.requires_local:
        return False
    if opt.compress_toggle is not None:
        return compress_enabled
    return True


def is_mode_runtime_available(
    opt: LlmModeOption,
    *,
    cloud_available: bool,
    local_available: bool,
    compress_enabled: bool,
) -> bool:
    if opt.requires_cloud and not cloud_available:
        return False
    if needs_local_at_runtime(opt, compress_enabled) and not local_available:
        return False
    return True


def mode_unavailable_hint(
    opt: LlmModeOption,
    *,
    cloud_available: bool,
    local_available: bool,
    compress_enabled: bool,
    local_model: str = "",
) -> str | None:
    if is_mode_runtime_available(
        opt,
        cloud_available=cloud_available,
        local_available=local_available,
        compress_enabled=compress_enabled,
    ):
        return None
    return validate_task_llm_config(
        llm_mode=opt.id,
        local_compress_enabled=compress_enabled if opt.compress_toggle is not None else False,
        local_model=local_model or None,
        cloud_available=cloud_available,
        local_available=local_available,
    )


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
        available = is_mode_runtime_available(
            opt,
            cloud_available=cloud_available,
            local_available=local_available,
            compress_enabled=default_compress_enabled,
        )
        item: dict[str, Any] = {
            "id": opt.id,
            "label": opt.label,
            "summary": opt.summary,
            "detail_bullets": list(opt.detail_bullets),
            "requires_cloud": opt.requires_cloud,
            "requires_local": opt.requires_local,
            "requires_llm": opt.requires_llm,
            "quality_warning": opt.quality_warning,
            "visualization_mode": opt.visualization_mode,
            "rerun_supported": opt.rerun_supported,
            "hide_token_stats": opt.hide_token_stats,
            "default": opt.id == norm_default,
            "available": available,
            "unavailable_hint": mode_unavailable_hint(
                opt,
                cloud_available=cloud_available,
                local_available=local_available,
                compress_enabled=default_compress_enabled,
                local_model=default_local_model,
            ),
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
        "availability_hints": get_availability_hints(),
    }


def validate_task_llm_config(
    *,
    llm_mode: str,
    local_compress_enabled: bool,
    local_model: str | None,
    cloud_available: bool,
    local_available: bool,
) -> str | None:
    """返回 None 表示合法，否则为错误说明。"""
    opt = get_llm_mode_option(llm_mode)
    if not opt.requires_llm:
        return None
    hints = get_availability_hints()
    if opt.requires_cloud and not cloud_available:
        return hints["cloud_unavailable"]
    if needs_local_at_runtime(opt, local_compress_enabled) and not local_available:
        if opt.compress_toggle is not None and local_compress_enabled:
            return hints["local_for_compress"]
        return hints["local_unavailable"]
    if needs_local_model_at_runtime(opt, local_compress_enabled) and not (local_model or "").strip():
        if opt.compress_toggle is not None:
            return hints["compress_model_required"]
        return hints["local_model_required"]
    return None
