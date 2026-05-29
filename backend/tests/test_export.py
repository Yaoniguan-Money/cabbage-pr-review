from app.models.schemas import InputType, TaskRecord, TaskResultSchema, RiskItem, RiskLevel, ConfidenceLevel
from app.services.export_md import export_markdown


def test_export_markdown_contains_sections():
    record = TaskRecord(
        input_type=InputType.PATCH,
        input_value="diff --git a/x b/x",
        result=TaskResultSchema(
            summary="测试摘要",
            summary_bullets=["要点1"],
            risks=[
                RiskItem(
                    id="r1",
                    title="风险",
                    description="描述",
                    risk_level=RiskLevel.MEDIUM,
                    confidence=ConfidenceLevel.HIGH,
                )
            ],
            degradation_notes=["局部降级说明"],
        ),
    )
    md = export_markdown(record)
    assert "# AI PR Review 报告" in md
    assert "## 摘要" in md
    assert "## 风险列表" in md
    assert "局部降级说明" in md
