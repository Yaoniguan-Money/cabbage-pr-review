from app.local.diagram_meta import (
    SCHEMA_DIAGRAM_TYPES,
    build_agent5_instruction,
    list_diagram_meta,
    resolve_diagram_title,
)
from app.models.schemas import DiagramData


def test_list_diagram_meta_has_all_types():
    meta = list_diagram_meta()
    ids = [t["id"] for t in meta["diagram_types"]]
    assert ids == list(SCHEMA_DIAGRAM_TYPES)
    assert meta["section_label"]
    assert meta["diagram_count"] == len(SCHEMA_DIAGRAM_TYPES)
    assert meta["ui_strings"]["render_error_title"]
    assert len(meta["default_legend"]) >= 3


def test_build_agent5_instruction_includes_type_ids():
    text = build_agent5_instruction()
    for dtype in SCHEMA_DIAGRAM_TYPES:
        assert dtype in text


def test_resolve_diagram_title_prefers_llm_title():
    d = DiagramData(diagram_type="architecture", title="自定义架构图")
    assert resolve_diagram_title(d) == "自定义架构图"


def test_resolve_diagram_title_fallback_to_meta():
    d = DiagramData(diagram_type="architecture", title="")
    assert resolve_diagram_title(d) == "原项目架构 / 流程图"
