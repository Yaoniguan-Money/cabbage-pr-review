from __future__ import annotations

from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_level(value: Any, *, default: str = "medium") -> str:
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"high", "medium", "low"}:
            return v
        if v in {"critical", "severe"}:
            return "high"
        if v in {"info", "minor"}:
            return "low"
        return default
    if isinstance(value, (int, float)):
        if value >= 0.75:
            return "high"
        if value >= 0.4:
            return "medium"
        return "low"
    return default


def _normalize_atom_plan_batch(data: dict[str, Any]) -> dict[str, Any]:
    plans = _ensure_list(data.get("plans"))
    normalized: list[dict[str, Any]] = []
    for idx, plan in enumerate(plans):
        if not isinstance(plan, dict):
            plan = {"atom_id": f"atom_{idx}"}
        concerns = [str(x) for x in _ensure_list(plan.get("new_concerns")) if str(x).strip()]
        normalized.append({**plan, "new_concerns": concerns})
    return {**data, "plans": normalized}


def _normalize_risk_review(data: dict[str, Any]) -> dict[str, Any]:
    risks = _ensure_list(data.get("risks"))
    normalized: list[dict[str, Any]] = []
    auto_fixed = 0
    for idx, risk in enumerate(risks):
        if not isinstance(risk, dict):
            risk = {"description": str(risk)}
        changed = False
        risk_id = risk.get("id")
        if not risk_id:
            risk_id = risk.get("atom_id") or f"risk_{uuid4().hex[:8]}"
            changed = True
        description = str(risk.get("description") or risk.get("evidence") or "").strip()
        if not description:
            description = "需要人工进一步确认的风险。"
            changed = True
        title = str(risk.get("title") or "").strip()
        if not title:
            title = f"风险项 {idx + 1}"
            changed = True
        related_atoms = [str(x) for x in _ensure_list(risk.get("related_atoms")) if str(x).strip()]
        atom_id = risk.get("atom_id")
        if atom_id and atom_id not in related_atoms:
            related_atoms = [str(atom_id), *related_atoms]
            changed = True
        fixed = {
            **risk,
            "id": str(risk_id),
            "title": title,
            "description": description,
            "risk_level": _normalize_level(risk.get("risk_level") or risk.get("level") or risk.get("severity")),
            "confidence": _normalize_level(risk.get("confidence")),
            "related_atoms": related_atoms,
            "file_paths": [str(x) for x in _ensure_list(risk.get("file_paths")) if str(x).strip()],
            "evidence": str(risk.get("evidence") or ""),
            "suggestion": str(risk.get("suggestion") or ""),
        }
        if changed:
            auto_fixed += 1
        normalized.append(fixed)
    notes = [str(x) for x in _ensure_list(data.get("degradation_notes")) if str(x).strip()]
    if auto_fixed:
        notes.append(f"result_repair 自动修复风险结构 {auto_fixed} 项（仅结构归一）")
    return {
        **data,
        "risks": normalized,
        "missing_info": _ensure_list(data.get("missing_info")),
        "degradation_notes": notes,
    }


def _normalize_diagram(data: dict[str, Any]) -> dict[str, Any]:
    nodes = _ensure_list(data.get("nodes"))
    normalized_nodes: list[dict[str, Any]] = []
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            node = {"label": str(node)}
        node_id = node.get("id") or f"n{idx}"
        normalized_nodes.append(
            {
                **node,
                "id": str(node_id),
                "label": str(node.get("label") or node_id),
                "group": str(node.get("group") or "default"),
                "risk": _normalize_level(node.get("risk"), default="medium")
                if node.get("risk") is not None
                else None,
                "confidence": _normalize_level(node.get("confidence"))
                if node.get("confidence") is not None
                else None,
            }
        )
    edges = _ensure_list(data.get("edges"))
    normalized_edges: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source") or edge.get("from")
        target = edge.get("target") or edge.get("to")
        if source is None or target is None:
            continue
        normalized_edges.append(
            {
                "source": str(source),
                "target": str(target),
                "label": str(edge.get("label") or ""),
            }
        )
    return {**data, "nodes": normalized_nodes, "edges": normalized_edges}


def _normalize_visualization(data: dict[str, Any]) -> dict[str, Any]:
    diagrams = _ensure_list(data.get("diagrams"))
    normalized_diagrams = [_normalize_diagram(d) for d in diagrams if isinstance(d, dict)]
    return {
        **data,
        "diagrams": normalized_diagrams,
        "summary_bullets": [str(x) for x in _ensure_list(data.get("summary_bullets")) if str(x).strip()],
        "detected_project_type": str(data.get("detected_project_type") or ""),
        "detected_framework": str(data.get("detected_framework") or ""),
    }


def repair_model(model: type[T], data: dict[str, Any]) -> T:
    """仅做结构修复，不做业务语义推断。"""
    if not isinstance(data, dict):
        raise ValueError("非 dict 结果")
    model_name = model.__name__
    if model_name == "AtomContextPlanBatch":
        data = _normalize_atom_plan_batch(data)
    elif model_name == "RiskReviewSchema":
        data = _normalize_risk_review(data)
    elif model_name == "VisualizationSchema":
        data = _normalize_visualization(data)
    elif model_name == "DiagramData":
        data = _normalize_diagram(data)
    return model.model_validate(data)
