from __future__ import annotations

from app.models.schemas import (
    InputType,
    TaskRecord,
    TaskResultSchema,
    TaskTokenStatsSchema,
    TokenStatsDisplaySegment,
)
from app.services.export_md import export_markdown


def test_export_includes_token_segments():
    record = TaskRecord(
        input_type=InputType.PATCH,
        input_value="diff",
        result=TaskResultSchema(summary="ok"),
        token_stats=TaskTokenStatsSchema(
            cloud_total_tokens=100,
            display_segments=[
                TokenStatsDisplaySegment(
                    key="cloud",
                    label="云端",
                    total_tokens=100,
                ),
            ],
        ),
    )
    md = export_markdown(record)
    assert "## Token 用量" in md
    assert "云端" in md
    assert "100" in md
