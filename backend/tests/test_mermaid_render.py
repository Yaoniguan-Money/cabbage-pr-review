from app.local.mermaid_render import render_diagram
from app.models.schemas import DiagramData, GraphEdge, GraphNode


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
