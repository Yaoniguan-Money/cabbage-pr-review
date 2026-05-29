"""审阅深度档位：Operational 参数与对外文案（单一数据源，无业务硬编码）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ReviewDepthMode = Literal["conservative", "balanced", "aggressive"]

VALID_MODES: frozenset[str] = frozenset({"conservative", "balanced", "aggressive"})


@dataclass(frozen=True)
class ReviewDepthProfile:
    mode: ReviewDepthMode
    atoms_per_batch: int
    max_batches_per_depth: int
    max_depth: int
    gap_fill_pro_calls_per_batch: int
    atom_priority_flash_call: bool


@dataclass(frozen=True)
class ReviewDepthOption:
    id: ReviewDepthMode
    label: str
    summary: str
    detail_bullets: tuple[str, ...]
    estimated_time: str
    cost_tier: Literal["low", "medium", "high"]
    default: bool


_PROFILES: dict[ReviewDepthMode, ReviewDepthProfile] = {
    "conservative": ReviewDepthProfile(
        mode="conservative",
        atoms_per_batch=15,
        max_batches_per_depth=1,
        max_depth=2,
        gap_fill_pro_calls_per_batch=0,
        atom_priority_flash_call=False,
    ),
    "balanced": ReviewDepthProfile(
        mode="balanced",
        atoms_per_batch=25,
        max_batches_per_depth=2,
        max_depth=2,
        gap_fill_pro_calls_per_batch=1,
        atom_priority_flash_call=True,
    ),
    "aggressive": ReviewDepthProfile(
        mode="aggressive",
        atoms_per_batch=25,
        max_batches_per_depth=4,
        max_depth=2,
        gap_fill_pro_calls_per_batch=1,
        atom_priority_flash_call=True,
    ),
}

_OPTIONS: tuple[ReviewDepthOption, ...] = (
    ReviewDepthOption(
        id="conservative",
        label="快速审阅",
        summary="改动少、赶时间时用；优先出结果，API 用量最低。",
        detail_bullets=(
            "每轮最多 15 个差异点，只跑 1 批",
            "不做遗漏风险补全的额外 Pro 调用",
            "大 PR 会在缺失信息中提示未扫完部分",
        ),
        estimated_time="约 3–5 分钟",
        cost_tier="low",
        default=False,
    ),
    ReviewDepthOption(
        id="balanced",
        label="标准审阅",
        summary="日常推荐；质量与 Token 成本平衡。",
        detail_bullets=(
            "每轮 25 个差异点，最多 2 批",
            "Flash 排序优先看重要变更",
            "每批最多 1 次补遗漏风险与 evidence",
        ),
        estimated_time="约 4–7 分钟",
        cost_tier="medium",
        default=True,
    ),
    ReviewDepthOption(
        id="aggressive",
        label="深度审阅",
        summary="大 PR 或重要合并前；尽量多扫差异点。",
        detail_bullets=(
            "每轮 25 个差异点，最多 4 批",
            "Flash 优先级排序 + 每批风险补全",
            "耗时与 API 用量最高，覆盖最广",
        ),
        estimated_time="约 6–10 分钟",
        cost_tier="high",
        default=False,
    ),
)


def normalize_review_depth_mode(mode: str | None, fallback: str = "balanced") -> ReviewDepthMode:
    if mode and mode in VALID_MODES:
        return mode  # type: ignore[return-value]
    if fallback in VALID_MODES:
        return fallback  # type: ignore[return-value]
    return "balanced"


def get_review_depth_profile(mode: str | None, fallback: str = "balanced") -> ReviewDepthProfile:
    key = normalize_review_depth_mode(mode, fallback)
    return _PROFILES[key]


def list_review_depth_options(default_mode: str = "balanced") -> list[dict]:
    norm_default = normalize_review_depth_mode(default_mode)
    out: list[dict] = []
    for opt in _OPTIONS:
        out.append(
            {
                "id": opt.id,
                "label": opt.label,
                "summary": opt.summary,
                "detail_bullets": list(opt.detail_bullets),
                "estimated_time": opt.estimated_time,
                "cost_tier": opt.cost_tier,
                "default": opt.id == norm_default,
            }
        )
    return out


def get_review_depth_option(mode: str | None, fallback: str = "balanced") -> ReviewDepthOption:
    key = normalize_review_depth_mode(mode, fallback)
    for opt in _OPTIONS:
        if opt.id == key:
            return opt
    return _OPTIONS[1]
