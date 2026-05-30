from __future__ import annotations

from app.llm.token_usage import (
    format_token_stats_display,
    get_task_token_stats,
    parse_openai_usage,
    parse_ollama_usage,
    record_token_usage,
    reset_task_token_usage,
)
from app.models.schemas import TokenStatsDisplaySegment


def test_parse_openai_usage():
    prompt, completion, est = parse_openai_usage(
        {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    )
    assert prompt == 10
    assert completion == 20
    assert est is False


def test_parse_ollama_usage_native():
    prompt, completion, est = parse_ollama_usage(
        {"prompt_eval_count": 100, "eval_count": 50},
        prompt_text="x",
        output_text="y",
    )
    assert prompt == 100
    assert completion == 50
    assert est is False


def test_record_and_aggregate():
    reset_task_token_usage()
    record_token_usage(tier="flash", prompt_tokens=100, completion_tokens=50)
    record_token_usage(tier="pro", prompt_tokens=200, completion_tokens=80)
    record_token_usage(tier="local_compress", prompt_tokens=30, completion_tokens=10, estimated=True)
    stats = get_task_token_stats()
    assert stats is not None
    assert stats.cloud_total_tokens == 430
    assert stats.local_total_tokens == 40
    assert stats.total_tokens == 470
    assert stats.estimated is True
    assert len(stats.by_tier) == 3
    assert len(stats.display_segments) >= 2
    labels = {s.key: s.label for s in stats.display_segments}
    assert "cloud" in labels
    assert "total" in labels


def test_format_display_segments_no_hardcode_in_frontend_contract():
    segs = format_token_stats_display(
        cloud_prompt=1,
        cloud_completion=2,
        cloud_total=3,
        local_prompt=0,
        local_completion=0,
        local_total=0,
        total=3,
        estimated=False,
    )
    assert all(isinstance(s, TokenStatsDisplaySegment) for s in segs)
    assert segs[0].label  # 后端单源文案非空
