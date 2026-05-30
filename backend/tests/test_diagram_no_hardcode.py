"""Mermaid 渲染层不得内联产品文案与颜色 hex。"""

from pathlib import Path


def test_mermaid_render_has_no_inline_hex_or_chinese_fallback():
    path = Path(__file__).resolve().parents[1] / "app" / "local" / "mermaid_render.py"
    text = path.read_text(encoding="utf-8")
    forbidden = ["#fee2e2", "#fef3c7", "#dbeafe", "未命名节点", "暂无结构数据", "变更前", "变更后", "变更区域"]
    for token in forbidden:
        assert token not in text, f"mermaid_render.py 发现禁止的内联字面量: {token}"
    assert "diagram_meta" in text
