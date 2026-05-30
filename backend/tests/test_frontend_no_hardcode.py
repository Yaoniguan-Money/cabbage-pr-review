"""前端展示层不得重复审阅深度 Token 文案（须由 API cost_tier_label 提供）。"""

from pathlib import Path


def test_input_page_has_no_cost_label_map():
    pages = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages"
    text = "\n".join(p.read_text(encoding="utf-8") for p in pages.glob("*.tsx") if "test" not in p.name)
    forbidden = ["COST_LABEL", "Token：省", "Token：适中", "Token：高"]
    for token in forbidden:
        assert token not in text, f"前端 pages 发现禁止的硬编码: {token}"
