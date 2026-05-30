import json
from pathlib import Path

from app.local.diagram_meta import SCHEMA_DIAGRAM_TYPES
from app.local.diagram_normalize import (
    build_global_compare_seed,
    merge_diagram_seeds,
    normalize_diagrams,
)
from app.local.result_repair import repair_model
from app.models.schemas import (
    DiagramData,
    DiffCompareSchema,
    GraphNode,
    ProjectIndexSchema,
    VisualizationSchema,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_normalize_diagrams_from_fixture():
    viz = repair_model(VisualizationSchema, _load("visualization.json"))
    diagrams = normalize_diagrams(viz.diagrams)
    assert len(diagrams) == len(SCHEMA_DIAGRAM_TYPES)
    types = {d.diagram_type for d in diagrams}
    assert types == set(SCHEMA_DIAGRAM_TYPES)
    for d in diagrams:
        assert d.mermaid.strip()


def test_merge_diagram_seeds_fills_missing_types():
    viz = repair_model(VisualizationSchema, _load("visualization.json"))
    only_path = [d for d in viz.diagrams if d.diagram_type == "path_compare"]
    seed_arch = DiagramData(
        diagram_type="architecture",
        nodes=[{"id": "s1", "label": "seed", "group": "module"}],
    )
    seed_impact = DiagramData(
        diagram_type="impact_overlay",
        nodes=[{"id": "i1", "label": "impact", "group": "module", "risk": "low"}],
    )
    seed_global = DiagramData(
        diagram_type="global_compare",
        nodes=[
            {"id": "gb1", "label": "before", "group": "before"},
            {"id": "ga1", "label": "after", "group": "after"},
        ],
    )
    merged = merge_diagram_seeds(only_path, seed_arch, seed_impact, seed_global)
    diagrams = normalize_diagrams(merged)
    assert len(diagrams) == len(SCHEMA_DIAGRAM_TYPES)
    by_type = {d.diagram_type: d for d in diagrams}
    assert by_type["architecture"].nodes[0].id == "s1"
    assert by_type["impact_overlay"].nodes[0].id == "i1"
    assert by_type["global_compare"].nodes[0].id == "gb1"


def test_build_global_compare_seed_from_modules():
    base = ProjectIndexSchema(version="base", modules=["app", "core"], entry_files=["main.py"])
    head = ProjectIndexSchema(version="head", modules=["app", "core"], entry_files=["main.py"])
    diff = DiffCompareSchema(all_atoms=[])
    seed = build_global_compare_seed(base, head, diff)
    assert seed is not None
    assert seed.diagram_type == "global_compare"
    groups = {n.group for n in seed.nodes}
    assert "before" in groups
    assert "after" in groups


def test_collect_path_compare_missing_groups_note():
    from app.local.diagram_meta import get_ui_strings
    from app.local.diagram_normalize import collect_diagram_structural_notes

    ui = get_ui_strings()
    bad = DiagramData(
        diagram_type="path_compare",
        nodes=[GraphNode(id="x", label="x", group="before")],
    )
    notes = collect_diagram_structural_notes([bad])
    assert ui.degradation_path_compare_missing_groups in notes


def test_collect_global_compare_missing_groups_note():
    from app.local.diagram_meta import get_ui_strings
    from app.local.diagram_normalize import collect_diagram_structural_notes

    ui = get_ui_strings()
    bad = DiagramData(
        diagram_type="global_compare",
        nodes=[GraphNode(id="x", label="x", group="before")],
    )
    notes = collect_diagram_structural_notes([bad])
    assert ui.degradation_global_compare_missing_groups in notes


def test_visualization_structural_notes_from_invalid_edges():
    raw = {
        "summary": "x",
        "diagrams": [
            {
                "diagram_type": "architecture",
                "nodes": [{"id": "a", "label": "A"}],
                "edges": [{"source": "a", "target": "missing", "label": "x"}],
            }
        ],
    }
    viz = repair_model(VisualizationSchema, raw)
    assert any("丢弃无效边" in n for n in viz.structural_notes)
