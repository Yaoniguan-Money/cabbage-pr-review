"""前端展示层不得重复审阅深度 Token 文案（须由 API cost_tier_label 提供）。"""

from pathlib import Path


def test_input_page_has_no_cost_label_map():
    pages = Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages"
    text = "\n".join(p.read_text(encoding="utf-8") for p in pages.glob("*.tsx") if "test" not in p.name)
    forbidden = ["COST_LABEL", "Token：省", "Token：适中", "Token：高"]
    for token in forbidden:
        assert token not in text, f"前端 pages 发现禁止的硬编码: {token}"


def test_frontend_has_no_diagram_title_map():
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    paths = list(root.glob("pages/*.tsx")) + list(root.glob("components/*.tsx"))
    text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in paths
        if "test" not in p.name and p.name != "MermaidDiagram.test.tsx"
    )
    forbidden = [
        "DIAGRAM_TITLES",
        "原项目架构 / 流程图",
        "PR 影响叠加图",
        "关键路径前后对比图",
    ]
    for token in forbidden:
        assert token not in text, f"前端发现禁止的图表标题硬编码: {token}"


def test_mermaid_diagram_has_no_inline_error_strings():
    path = Path(__file__).resolve().parents[2] / "frontend" / "src" / "components" / "MermaidDiagram.tsx"
    text = path.read_text(encoding="utf-8")
    forbidden = ["图表渲染失败", "展开查看原始 Mermaid", "FALLBACK_UI", "render error"]
    for token in forbidden:
        assert token not in text, f"MermaidDiagram 发现禁止的内联文案: {token}"


def test_changed_pages_have_no_hardcoded_meta_constants():
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    paths = [
        root / "pages" / "InputPage.tsx",
        root / "pages" / "DetailPage.tsx",
        root / "components" / "DiagramCard.tsx",
        root / "api" / "client.ts",
    ]
    text = "\n".join(p.read_text(encoding="utf-8") for p in paths if p.is_file())
    forbidden = [
        "PROJECT_TYPES",
        "FRAMEWORKS",
        '?? "',
        "风险列表（前 5 条）",
        "节点摘要（",
        "导出 Markdown",
        "无法加载审阅深度选项",
        "无法加载推理模式选项",
        "创建任务失败",
    ]
    for token in forbidden:
        assert token not in text, f"变更区前端发现禁止硬编码: {token}"

