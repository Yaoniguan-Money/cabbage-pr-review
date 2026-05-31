"""评委演示 Patch：API 与三套场景真实规则命中回归。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.local.demo_patches_meta import list_demo_patches
from app.local.file_io import parse_patch_text
from app.main import app
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review

client = TestClient(app)


def _hits_from_patch_text(patch_text: str) -> set[str]:
    patches = parse_patch_text(patch_text)
    ctx = {
        "patches": patches,
        "file_paths": [p["filename"] for p in patches],
    }
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    return {hit.rule_id for hit in hits}


def test_demo_patches_api():
    resp = client.get("/api/demo-patches")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["scenarios"]) == 3
    for scenario in body["scenarios"]:
        assert scenario["id"]
        assert scenario["title"]
        assert scenario["patch_text"].strip()
        assert scenario["expected_rule_ids"]
        assert isinstance(scenario.get("context_overlay"), dict)


def test_demo_patches_meta_matches_api():
    api_body = client.get("/api/demo-patches").json()
    meta_body = list_demo_patches()
    assert api_body == meta_body


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
def test_demo_scenario_triggers_expected_rules(scenario_id: str, expected_rules: set[str]):
    scenarios = list_demo_patches()["scenarios"]
    scenario = next(s for s in scenarios if s["id"] == scenario_id)
    hits = _hits_from_patch_text(scenario["patch_text"])
    assert expected_rules <= hits
    assert set(scenario["expected_rule_ids"]) == expected_rules


def test_s3_governance_end_to_end_review():
    scenarios = list_demo_patches()["scenarios"]
    s3 = next(s for s in scenarios if s["id"] == "S3-governance")
    from app.local.file_io import parse_patch_text

    patches = parse_patch_text(s3["patch_text"])
    ctx = {"patches": patches, "file_paths": [p["filename"] for p in patches]}
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    hit_ids = {h.rule_id for h in hits}
    assert "test-file-removed" in hit_ids
