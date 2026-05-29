from __future__ import annotations

from app.local.mermaid_render import render_diagram
from app.models.schemas import DiagramData


def attach_mermaid(diagram: DiagramData | None) -> DiagramData | None:
    if diagram is None:
        return None
    if not diagram.mermaid and diagram.nodes:
        diagram.mermaid = render_diagram(diagram)
    return diagram


def attach_mermaid_list(diagrams: list[DiagramData]) -> list[DiagramData]:
    return [attach_mermaid(d) or d for d in diagrams]
