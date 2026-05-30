"""单任务 Token 累计：tier 与展示文案单源，供 Provider/router/compress 写入。"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Literal

from app.models.schemas import (
    TaskTokenStatsSchema,
    TokenStatsDisplaySegment,
    TokenUsageByTier,
)

TokenTier = Literal["flash", "pro", "local_compress", "local_flash", "local_pro"]

VALID_TOKEN_TIERS: frozenset[str] = frozenset(
    {"flash", "pro", "local_compress", "local_flash", "local_pro"}
)

CLOUD_TIERS: frozenset[str] = frozenset({"flash", "pro"})
LOCAL_TIERS: frozenset[str] = frozenset({"local_compress", "local_flash", "local_pro"})

# 展示文案单源（前端/导出只读 display_segments，禁止 duplicate）
_DISPLAY_LABELS: dict[str, str] = {
    "cloud": "云端",
    "local": "本地",
    "total": "合计",
}
_ESTIMATED_SUFFIX = "约"


@dataclass
class _TierBucket:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated: bool = False


@dataclass
class _TaskTokenAccumulator:
    tiers: dict[str, _TierBucket] = field(default_factory=dict)
    any_estimated: bool = False

    def record(
        self,
        *,
        tier: str,
        prompt_tokens: int,
        completion_tokens: int,
        estimated: bool = False,
    ) -> None:
        if tier not in VALID_TOKEN_TIERS:
            return
        bucket = self.tiers.setdefault(tier, _TierBucket())
        bucket.calls += 1
        bucket.prompt_tokens += max(0, prompt_tokens)
        bucket.completion_tokens += max(0, completion_tokens)
        if estimated:
            bucket.estimated = True
            self.any_estimated = True


_task_token_acc: ContextVar[_TaskTokenAccumulator | None] = ContextVar(
    "task_token_acc", default=None
)


def reset_task_token_usage() -> None:
    _task_token_acc.set(_TaskTokenAccumulator())


def _get_acc() -> _TaskTokenAccumulator:
    acc = _task_token_acc.get()
    if acc is None:
        acc = _TaskTokenAccumulator()
        _task_token_acc.set(acc)
    return acc


def record_token_usage(
    *,
    tier: str,
    prompt_tokens: int,
    completion_tokens: int,
    estimated: bool = False,
) -> None:
    _get_acc().record(
        tier=tier,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated=estimated,
    )


def parse_openai_usage(usage: dict | None) -> tuple[int, int, bool]:
    """返回 (prompt, completion, estimated)。"""
    if not usage or not isinstance(usage, dict):
        return 0, 0, False
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    if prompt == 0 and completion == 0 and usage.get("total_tokens"):
        total = int(usage["total_tokens"])
        return total // 2, total - total // 2, True
    return prompt, completion, False


def parse_ollama_usage(
    data: dict,
    *,
    prompt_text: str,
    output_text: str,
) -> tuple[int, int, bool]:
    prompt = data.get("prompt_eval_count")
    completion = data.get("eval_count")
    if prompt is not None and completion is not None:
        return int(prompt), int(completion), False
    est_prompt = max(1, len(prompt_text) // 4) if prompt_text else 0
    est_completion = max(1, len(output_text) // 4) if output_text else 0
    return est_prompt, est_completion, True


def format_token_stats_display(
    *,
    cloud_prompt: int,
    cloud_completion: int,
    cloud_total: int,
    local_prompt: int,
    local_completion: int,
    local_total: int,
    total: int,
    estimated: bool,
) -> list[TokenStatsDisplaySegment]:
    segments: list[TokenStatsDisplaySegment] = []
    if cloud_total > 0 or cloud_prompt > 0 or cloud_completion > 0:
        segments.append(
            TokenStatsDisplaySegment(
                key="cloud",
                label=_DISPLAY_LABELS["cloud"],
                prompt_tokens=cloud_prompt,
                completion_tokens=cloud_completion,
                total_tokens=cloud_total,
            )
        )
    if local_total > 0 or local_prompt > 0 or local_completion > 0:
        segments.append(
            TokenStatsDisplaySegment(
                key="local",
                label=_DISPLAY_LABELS["local"],
                prompt_tokens=local_prompt,
                completion_tokens=local_completion,
                total_tokens=local_total,
            )
        )
    if total > 0:
        label = _DISPLAY_LABELS["total"]
        if estimated:
            label = f"{label}（{_ESTIMATED_SUFFIX}）"
        segments.append(
            TokenStatsDisplaySegment(
                key="total",
                label=label,
                prompt_tokens=cloud_prompt + local_prompt,
                completion_tokens=cloud_completion + local_completion,
                total_tokens=total,
            )
        )
    return segments


def get_task_token_stats() -> TaskTokenStatsSchema | None:
    acc = _task_token_acc.get()
    if not acc or not acc.tiers:
        return None

    by_tier: list[TokenUsageByTier] = []
    cloud_prompt = cloud_completion = 0
    local_prompt = local_completion = 0

    for tier_id in sorted(acc.tiers.keys()):
        b = acc.tiers[tier_id]
        total = b.prompt_tokens + b.completion_tokens
        by_tier.append(
            TokenUsageByTier(
                tier=tier_id,  # type: ignore[arg-type]
                calls=b.calls,
                prompt_tokens=b.prompt_tokens,
                completion_tokens=b.completion_tokens,
                total_tokens=total,
            )
        )
        if tier_id in CLOUD_TIERS:
            cloud_prompt += b.prompt_tokens
            cloud_completion += b.completion_tokens
        elif tier_id in LOCAL_TIERS:
            local_prompt += b.prompt_tokens
            local_completion += b.completion_tokens

    cloud_total = cloud_prompt + cloud_completion
    local_total = local_prompt + local_completion
    total = cloud_total + local_total
    if total <= 0 and not any(b.calls for b in acc.tiers.values()):
        return None

    return TaskTokenStatsSchema(
        cloud_prompt_tokens=cloud_prompt,
        cloud_completion_tokens=cloud_completion,
        cloud_total_tokens=cloud_total,
        local_prompt_tokens=local_prompt,
        local_completion_tokens=local_completion,
        local_total_tokens=local_total,
        total_tokens=total,
        estimated=acc.any_estimated,
        by_tier=by_tier,
        display_segments=format_token_stats_display(
            cloud_prompt=cloud_prompt,
            cloud_completion=cloud_completion,
            cloud_total=cloud_total,
            local_prompt=local_prompt,
            local_completion=local_completion,
            local_total=local_total,
            total=total,
            estimated=acc.any_estimated,
        ),
    )
