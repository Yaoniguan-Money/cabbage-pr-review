"""Demo patch 与 sidecar 对齐、体量门槛回归。"""

from __future__ import annotations

import re

import pytest

from app.local.demo_patch_stats import assert_demo_patch_thresholds, count_patch_stats
from app.local.demo_patches_meta import list_demo_patches, merge_demo_context_overlay
from app.local.file_io import parse_patch_text
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review

PLACEHOLDER_PATTERNS = (
    re.compile(r"extra_\d+"),
    re.compile(r"step_\d+"),
    re.compile(r"stable_block_"),
    re.compile(r"=\s*\w+\s+value\s+\d"),
    re.compile(r"(FEATURE|OPTION|SECRET|TAIL|auth_helper|boot_|line_|add_|grow_)_\d+"),
)
from app.local.demo_patches_meta import list_demo_patches, merge_demo_context_overlay
from app.local.file_io import parse_patch_text
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review


def _patch_paths(patch_text: str) -> set[str]:
    stats = count_patch_stats(patch_text)
    return set(stats["file_paths"])


def _hits_from_patch_text(patch_text: str) -> set[str]:
    patches = parse_patch_text(patch_text)
    ctx = {"patches": patches, "file_paths": [p["filename"] for p in patches]}
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    return {hit.rule_id for hit in hits}


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_patch_meets_volume_thresholds(scenario_id: str):
    scenario = next(s for s in list_demo_patches()["scenarios"] if s["id"] == scenario_id)
    assert_demo_patch_thresholds(scenario["patch_text"], label=scenario_id)


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_sidecar_paths_align_with_patch(scenario_id: str):
    scenario = next(s for s in list_demo_patches()["scenarios"] if s["id"] == scenario_id)
    overlay = scenario.get("context_overlay") or {}
    patch_files = _patch_paths(scenario["patch_text"])

    for key in ("path_compare_focus", "file_to_node"):
        values = overlay.get(key) or {}
        paths = values if isinstance(values, list) else list(values.keys())
        for path in paths:
            normalized = str(path).replace("\\", "/")
            assert normalized in patch_files, f"{scenario_id}: {key} 引用 {path} 不在 patch 中"

    tree = overlay.get("directory_tree") or []
    assert tree, f"{scenario_id}: directory_tree 为空"
    assert any(str(p).replace("\\", "/") in patch_files for p in tree)


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_sidecar_has_summary_and_readme(scenario_id: str):
    scenario = next(s for s in list_demo_patches()["scenarios"] if s["id"] == scenario_id)
    overlay = scenario.get("context_overlay") or {}
    assert str(overlay.get("summary_line") or "").strip()
    bullets = overlay.get("summary_bullets") or []
    assert isinstance(bullets, list) and len(bullets) >= 2
    assert str(overlay.get("readme") or "").strip()
    assert overlay.get("architecture_seed")


@pytest.mark.parametrize(
    ("scenario_id", "expected_rules"),
    [
        ("S1-security", {"patch-hardcoded-secret", "eval-or-exec"}),
        ("S2-change-surface", {"dockerfile-changed", "dockerfile-root-user", "ci-config-changed"}),
        (
            "S3-governance",
            {"lockfile-changed", "requirements-unpinned", "test-file-removed"},
        ),
    ],
)
def test_demo_rules_exact_match(scenario_id: str, expected_rules: set[str]):
    scenario = next(s for s in list_demo_patches()["scenarios"] if s["id"] == scenario_id)
    hits = _hits_from_patch_text(scenario["patch_text"])
    assert hits == expected_rules


def test_merge_overlay_injects_summary_into_context():
    ctx = merge_demo_context_overlay({}, "S1-security")
    assert str(ctx.get("summary_line") or "").strip()
    assert ctx.get("architecture_seed")
    assert ctx.get("index_modules")


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_patch_has_no_placeholder_lines(scenario_id: str):
    scenario = next(s for s in list_demo_patches()["scenarios"] if s["id"] == scenario_id)
    for line in scenario["patch_text"].splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        for pattern in PLACEHOLDER_PATTERNS:
            assert not pattern.search(body), f"{scenario_id}: 占位行 {body[:80]!r}"


@pytest.mark.parametrize("scenario_id", ["S1-security", "S2-change-surface", "S3-governance"])
def test_demo_patch_added_lines_look_like_real_code(scenario_id: str):
    scenario = next(s for s in list_demo_patches()["scenarios"] if s["id"] == scenario_id)
    added = [
        ln[1:]
        for ln in scenario["patch_text"].splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    ]
    signals = sum(
        1
        for ln in added
        if any(kw in ln for kw in ("def ", "class ", "import ", "assert ", "return ", "FROM ", "runs-on:"))
    )
    assert signals >= 20, f"{scenario_id}: 真实代码信号过少 ({signals})"
