"""评委演示 Patch 场景元数据单源（禁止在前端硬编码场景文案与 patch 内容）。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DemoPatchScenario:
    id: str
    title: str
    description: str
    patch_filename: str
    context_filename: str
    expected_rule_ids: tuple[str, ...]


_SCENARIOS: tuple[DemoPatchScenario, ...] = (
    DemoPatchScenario(
        id="S1-security",
        title="S1 安全综合",
        description="硬编码密钥（config/settings.py）+ eval 执行（app/runtime/executor.py），10 文件多 hunk 变更",
        patch_filename="S1-security.patch",
        context_filename="S1-security.context.json",
        expected_rule_ids=("patch-hardcoded-secret", "eval-or-exec"),
    ),
    DemoPatchScenario(
        id="S2-change-surface",
        title="S2 变更面",
        description="Dockerfile 变更 + USER root + CI 工作流扩展，覆盖构建/部署 9 文件",
        patch_filename="S2-change-surface.patch",
        context_filename="S2-change-surface.context.json",
        expected_rule_ids=("dockerfile-changed", "dockerfile-root-user", "ci-config-changed"),
    ),
    DemoPatchScenario(
        id="S3-governance",
        title="S3 工程治理",
        description="锁文件漂移、requirements 未 pin、测试大量删除，10 文件治理场景",
        patch_filename="S3-governance.patch",
        context_filename="S3-governance.context.json",
        expected_rule_ids=(
            "lockfile-changed",
            "requirements-unpinned",
            "test-file-removed",
        ),
    ),
)

_SCENARIO_BY_ID: dict[str, DemoPatchScenario] = {s.id: s for s in _SCENARIOS}


def _demo_patches_dir() -> Path:
    override = os.environ.get("DEMO_PATCHES_DIR", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "data" / "demo"


def _read_patch_text(filename: str) -> str:
    path = _demo_patches_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(f"演示 Patch 文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def _read_context_overlay(filename: str) -> dict[str, Any]:
    path = _demo_patches_dir() / filename
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_scenario_by_id(scenario_id: str) -> dict[str, Any] | None:
    scenario = _SCENARIO_BY_ID.get(scenario_id)
    if not scenario:
        return None
    return {
        "id": scenario.id,
        "title": scenario.title,
        "description": scenario.description,
        "expected_rule_ids": list(scenario.expected_rule_ids),
        "patch_text": _read_patch_text(scenario.patch_filename),
        "context_overlay": _read_context_overlay(scenario.context_filename),
    }


def merge_demo_context_overlay(pr_context: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        return pr_context
    overlay = scenario.get("context_overlay") or {}
    if not overlay:
        return pr_context
    merged = dict(pr_context)
    for key in (
        "directory_tree",
        "entry_files",
        "path_compare_focus",
        "architecture_seed",
        "file_to_node",
        "readme",
        "index_modules",
        "index_routes",
        "summary_line",
        "summary_bullets",
    ):
        if key in overlay:
            merged[key] = overlay[key]
    if overlay.get("directory_tree"):
        merged["tree"] = overlay["directory_tree"]
    return merged


def list_demo_patches() -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    for scenario in _SCENARIOS:
        scenarios.append(
            {
                "id": scenario.id,
                "title": scenario.title,
                "description": scenario.description,
                "expected_rule_ids": list(scenario.expected_rule_ids),
                "patch_text": _read_patch_text(scenario.patch_filename),
                "context_overlay": _read_context_overlay(scenario.context_filename),
            }
        )
    return {"scenarios": scenarios}
