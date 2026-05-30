"""评委演示 Patch 场景元数据单源（禁止在前端硬编码场景文案与 patch 内容）。"""

from __future__ import annotations

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
    expected_rule_ids: tuple[str, ...]


_SCENARIOS: tuple[DemoPatchScenario, ...] = (
    DemoPatchScenario(
        id="S1-security",
        title="S1 安全综合",
        description="硬编码密钥 + 动态执行：展示 HIGH severity 安全规则并行命中",
        patch_filename="S1-security.patch",
        expected_rule_ids=("patch-hardcoded-secret", "eval-or-exec"),
    ),
    DemoPatchScenario(
        id="S2-change-surface",
        title="S2 变更面",
        description="Dockerfile USER root（match.all）+ CI 配置变更",
        patch_filename="S2-change-surface.patch",
        expected_rule_ids=("dockerfile-root-user", "ci-config-changed"),
    ),
    DemoPatchScenario(
        id="S3-governance",
        title="S3 工程治理",
        description="锁文件变更、未固定依赖版本、测试大量移除",
        patch_filename="S3-governance.patch",
        expected_rule_ids=(
            "lockfile-changed",
            "requirements-unpinned",
            "test-file-removed",
        ),
    ),
)


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
            }
        )
    return {"scenarios": scenarios}
