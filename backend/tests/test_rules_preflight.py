"""规则预检与 LLM 集成测试。"""

from __future__ import annotations

from app.rules.pipeline.rules_preflight import format_rule_hits_for_prompt, run_rules_preflight
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.rule_schema import RuleHitRecord


def test_format_rule_hits_for_prompt():
    hits = [
        RuleHitRecord(
            rule_id="patch-hardcoded-secret",
            severity="HIGH",
            file_path="a.py",
            evidence="password = x",
            message="密钥",
        )
    ]
    rows = format_rule_hits_for_prompt(hits)
    assert rows[0]["rule_id"] == "patch-hardcoded-secret"
    assert "password" in rows[0]["evidence"]


def test_run_rules_preflight_detects_secret():
    patch = """@@ -1,2 +1,3 @@
+password = "test-only-placeholder"
"""
    ctx = {
        "patches": [{"filename": "config.py", "status": "modified", "patch": patch}],
    }
    diff, _ = run_rules_diff(ctx)
    hits, notes = run_rules_preflight(diff, ctx)
    assert len(hits) >= 1
    assert any("预检" in n for n in notes)
