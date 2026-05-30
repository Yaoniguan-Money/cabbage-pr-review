"""Mermaid 渲染层不得内联产品文案与颜色 hex。"""

from pathlib import Path


def test_mermaid_render_has_no_inline_hex_or_chinese_fallback():
    path = Path(__file__).resolve().parents[1] / "app" / "local" / "mermaid_render.py"
    text = path.read_text(encoding="utf-8")
    forbidden = ["#fee2e2", "#fef3c7", "#dbeafe", "未命名节点", "暂无结构数据", "变更前", "变更后", "变更区域"]
    for token in forbidden:
        assert token not in text, f"mermaid_render.py 发现禁止的内联字面量: {token}"
    assert "diagram_meta" in text


def test_diagram_card_has_no_inline_chinese_labels():
    path = Path(__file__).resolve().parents[2] / "frontend" / "src" / "components" / "DiagramCard.tsx"
    text = path.read_text(encoding="utf-8")
    forbidden = ["节点摘要", " · 风险 ", " · 置信 "]
    for token in forbidden:
        assert token not in text, f"DiagramCard 发现禁止的内联文案: {token}"
    assert "uiStrings" in text

