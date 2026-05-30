from app.local.mermaid_render import render_diagram
from app.models.schemas import ConfidenceLevel, DiagramData, GraphEdge, GraphNode


def test_render_diagram_sanitizes_node_ids_and_edge_labels():
    data = DiagramData(
        diagram_type="architecture",
        nodes=[GraphNode(id="backend/api.v1", label='Backend "API"', group="core")],
        edges=[GraphEdge(source="backend/api.v1", target="backend/api.v1", label='calls(a|b)')],
    )
    mermaid = render_diagram(data)
    assert 'backend_api_v1["Backend \'API\'"]' in mermaid
    assert '-->|"calls(a/b)"| backend_api_v1' in mermaid


def test_render_path_compare_uses_safe_subgraph_ids():
    data = DiagramData(
        diagram_type="path_compare",
        nodes=[
            GraphNode(id="before-1", label="变更前模块", group="before"),
            GraphNode(id="after-1", label="变更后模块", group="after"),
        ],
        edges=[GraphEdge(source="before-1", target="after-1", label="变更")],
    )
    mermaid = render_diagram(data)
    assert "subgraph before_nodes [变更前]" in mermaid
    assert "subgraph after_nodes [变更后]" in mermaid
    assert "before_1" in mermaid and "after_1" in mermaid


def test_render_escapes_mermaid_reserved_node_id_graph():
    """LLM 常产出 id=graph 表示 workflow，须逃逸否则 Mermaid 11 解析失败。"""
    data = DiagramData(
        diagram_type="architecture",
        nodes=[
            GraphNode(id="app", label="app"),
            GraphNode(id="graph", label="graph (workflow)"),
        ],
        edges=[GraphEdge(source="app", target="graph", label="workflow_app")],
    )
    mermaid = render_diagram(data)
    lines = [ln.strip() for ln in mermaid.splitlines()]
    assert any(ln.startswith('n_graph["') for ln in lines)
    assert not any(ln.startswith('graph["') for ln in lines)
    assert "app -->|" in mermaid and "n_graph" in mermaid


def test_render_escapes_reserved_end_and_class():
    data = DiagramData(
        diagram_type="architecture",
        nodes=[
            GraphNode(id="end", label="结束"),
            GraphNode(id="class", label="类"),
        ],
        edges=[],
    )
    mermaid = render_diagram(data)
    assert 'n_end["结束"]' in mermaid
    assert 'n_class["类"]' in mermaid


def test_render_impact_overlay_uses_changed_subgraph():
    data = DiagramData(
        diagram_type="impact_overlay",
        nodes=[
            GraphNode(id="m1", label="模块A", risk="high"),
            GraphNode(id="m2", label="模块B"),
        ],
        edges=[GraphEdge(source="m1", target="m2", label="依赖")],
    )
    arch = render_diagram(DiagramData(diagram_type="architecture", nodes=data.nodes, edges=data.edges))
    impact = render_diagram(data)
    assert "subgraph changed_area" in impact
    assert impact != arch


def test_render_path_compare_appends_confidence_suffix():
    data = DiagramData(
        diagram_type="path_compare",
        nodes=[
            GraphNode(id="b1", label="旧路径", group="before", confidence=ConfidenceLevel.HIGH),
            GraphNode(id="a1", label="新路径", group="after", confidence=ConfidenceLevel.MEDIUM),
        ],
        edges=[GraphEdge(source="b1", target="a1", label="替换")],
    )
    mermaid = render_diagram(data)
    assert "高置信" in mermaid
    assert "中置信" in mermaid


def test_render_global_compare_uses_meta_subgraph_titles():
    from app.local.diagram_meta import get_ui_strings

    ui = get_ui_strings()
    data = DiagramData(
        diagram_type="global_compare",
        nodes=[
            GraphNode(id="before-1", label="模块A", group="before"),
            GraphNode(id="after-1", label="模块A", group="after", risk="medium"),
        ],
        edges=[GraphEdge(source="before-1", target="after-1", label="演进")],
    )
    mermaid = render_diagram(data)
    assert f"subgraph global_before [{ui.global_compare_before}]" in mermaid
    assert f"subgraph global_after [{ui.global_compare_after}]" in mermaid
    assert "subgraph before_nodes" not in mermaid
    assert ":::globalBefore" in mermaid
    assert ":::riskMed" in mermaid


def test_render_architecture_uses_module_default_and_confidence():
    data = DiagramData(
        diagram_type="architecture",
        nodes=[
            GraphNode(id="m1", label="模块", group="module", confidence=ConfidenceLevel.HIGH),
        ],
        edges=[],
    )
    mermaid = render_diagram(data)
    assert ":::moduleDefault" in mermaid
    assert "高置信" in mermaid
