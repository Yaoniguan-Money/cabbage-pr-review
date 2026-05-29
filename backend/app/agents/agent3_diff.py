from __future__ import annotations

from uuid import uuid4

from app.agents.base import extract_modules_from_paths
from app.local.mermaid_render import diagram_from_modules, render_diagram
from app.models.schemas import DiffAtom, DiffCompareSchema, ProjectIndexSchema


def _atom_from_patch(p: dict) -> DiffAtom:
    fn = p.get("filename", "unknown")
    status = p.get("status", "modified")
    change = "modified"
    if status == "added":
        change = "added"
    elif status == "removed":
        change = "removed"
    elif status == "renamed":
        change = "renamed"
    patch = p.get("patch") or ""
    symbol = ""
    for line in patch.splitlines()[:30]:
        if line.startswith("+def ") or line.startswith("+class "):
            symbol = line.strip()[:80]
            break
        if line.startswith("+export ") or line.startswith("+function "):
            symbol = line.strip()[:80]
            break
    return DiffAtom(
        id=str(uuid4())[:8],
        file_path=fn,
        change_type=change,
        symbol=symbol,
        route_or_api="",
        dependency_hint="",
        summary=f"{change} {fn}" + (f" ({symbol})" if symbol else ""),
    )


def run_agent3(base: ProjectIndexSchema, head: ProjectIndexSchema, pr_context: dict) -> DiffCompareSchema:
    patches = pr_context.get("patches", [])
    file_atoms = [_atom_from_patch(p) for p in patches[:50]]
    func_atoms = [a for a in file_atoms if a.symbol][:20]
    route_atoms = [
        DiffAtom(
            id=str(uuid4())[:8],
            file_path="routes",
            change_type="modified",
            route_or_api=r,
            summary=r[:100],
        )
        for r in head.routes[:10]
    ]
    dep_atoms: list[DiffAtom] = []
    for line in " ".join(p.get("patch", "") for p in patches).splitlines():
        if "requirements" in line or "package.json" in line or "import " in line:
            dep_atoms.append(
                DiffAtom(
                    id=str(uuid4())[:8],
                    file_path="dependencies",
                    change_type="modified",
                    dependency_hint=line.strip()[:100],
                    summary=line.strip()[:100],
                )
            )
            if len(dep_atoms) >= 5:
                break
    all_atoms = file_atoms + func_atoms + route_atoms + dep_atoms
    impacted = set(extract_modules_from_paths([a.file_path for a in file_atoms]))
    impact = diagram_from_modules("impact_overlay", head.modules, head.routes, impacted)
    impact.mermaid = render_diagram(impact)
    return DiffCompareSchema(
        file_diffs=file_atoms,
        function_diffs=func_atoms,
        route_diffs=route_atoms,
        dependency_diffs=dep_atoms,
        impact_diagram=impact,
        all_atoms=all_atoms,
    )
