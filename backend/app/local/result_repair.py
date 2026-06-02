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


def _normalize_diff_atom(atom: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
    symbols = [str(x) for x in _ensure_list(atom.get("affected_symbols")) if str(x).strip()]
    atom_id = str(atom.get("id") or f"atom_{uuid4().hex[:8]}")
    file_path = str(atom.get("file_path") or atom.get("filename") or atom.get("file") or f"unknown_{index}")
    change_type = str(atom.get("change_type") or atom.get("status") or "modified")
    if change_type not in {"added", "modified", "removed", "renamed"}:
        change_type = "modified"
    symbol = str(atom.get("symbol") or atom.get("name") or "")
    return {
        **atom,
        "id": atom_id,
        "file_path": file_path.replace("\\", "/"),
        "change_type": change_type,
        "symbol": symbol,
        "affected_symbols": symbols,
    }


def _normalize_diff_compare(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    for key in ("file_diffs", "function_diffs", "route_diffs", "dependency_diffs", "all_atoms"):
        items = _ensure_list(data.get(key))
        out[key] = [_normalize_diff_atom(x, index=i) if isinstance(x, dict) else x for i, x in enumerate(items)]
    if isinstance(out.get("impact_diagram"), dict):
        out["impact_diagram"] = _normalize_diagram(out["impact_diagram"])
    return out


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
    node_ids = {n["id"] for n in normalized_nodes}
    edges = _ensure_list(data.get("edges"))
    normalized_edges: list[dict[str, Any]] = []
    dropped_edges = 0
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source") or edge.get("from")
        target = edge.get("target") or edge.get("to")
        if source is None or target is None:
            dropped_edges += 1
            continue
        source_s = str(source)
        target_s = str(target)
        if source_s not in node_ids or target_s not in node_ids:
            dropped_edges += 1
            continue
        normalized_edges.append(
            {
                "source": source_s,
                "target": target_s,
                "label": str(edge.get("label") or ""),
            }
        )
    legend = _ensure_list(data.get("legend"))
    normalized_legend: list[dict[str, Any]] = []
    for item in legend:
        if isinstance(item, dict) and item.get("key") and item.get("label"):
            normalized_legend.append(
                {
                    "key": str(item["key"]),
                    "label": str(item["label"]),
                    "color": str(item.get("color") or ""),
                }
            )
    out = {
        **data,
        "title": str(data.get("title") or ""),
        "caption": str(data.get("caption") or ""),
        "legend": normalized_legend,
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }
    if dropped_edges:
        notes = _ensure_list(data.get("_repair_notes"))
        notes.append(f"result_repair 丢弃无效边 {dropped_edges} 条（端点不在 nodes 内）")
        out["_repair_notes"] = notes
    return out


def _normalize_visualization(data: dict[str, Any]) -> dict[str, Any]:
    diagrams = _ensure_list(data.get("diagrams"))
    structural_notes = [str(x) for x in _ensure_list(data.get("structural_notes")) if str(x).strip()]
    normalized_diagrams: list[dict[str, Any]] = []
    for d in diagrams:
        if not isinstance(d, dict):
            continue
        nd = _normalize_diagram(d)
        for note in _ensure_list(nd.pop("_repair_notes", None)):
            text = str(note).strip()
            if text:
                structural_notes.append(text)
        normalized_diagrams.append(nd)
    return {
        **data,
        "diagrams": normalized_diagrams,
        "structural_notes": structural_notes,
        "summary_bullets": [str(x) for x in _ensure_list(data.get("summary_bullets")) if str(x).strip()],
        "detected_project_type": str(data.get("detected_project_type") or ""),
        "detected_framework": str(data.get("detected_framework") or ""),
    }


def repair_model(model: type[T], data: dict[str, Any]) -> T:
    """仅做结构修复，不做业务语义推断。"""
    if not isinstance(data, dict):
        raise ValueError("非 dict 结果")
    model_name = model.__name__
    if model_name == "DiffCompareSchema":
        data = _normalize_diff_compare(data)
    elif model_name == "AtomContextPlanBatch":
        data = _normalize_atom_plan_batch(data)
    elif model_name == "RiskReviewSchema":
        data = _normalize_risk_review(data)
    elif model_name == "VisualizationSchema":
        data = _normalize_visualization(data)
    elif model_name == "DiagramData":
        data = _normalize_diagram(data)
    return model.model_validate(data)
