"""规则模式相关测试。"""

from __future__ import annotations

from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review
from app.rules.rule_loader import load_rule_pack
from app.rules.rule_evaluator import locate_added_evidence_lines


def test_load_default_rule_pack():
    rules, config = load_rule_pack()
    assert len(rules) >= 10
    assert config.scope.max_atoms_per_run >= 50


def test_default_pack_dir_inside_app_package():
    from app.rules.rule_loader import _DEFAULT_PACK_DIR, resolve_rules_pack_dir

    assert _DEFAULT_PACK_DIR.name == "default"
    assert "packs" in _DEFAULT_PACK_DIR.parts
    assert resolve_rules_pack_dir().is_dir()


def test_rules_diff_from_patch():
    patch = """diff --git a/app/main.py b/app/main.py
index 111..222 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
 import os
+API_KEY = "sk-test-placeholder-not-a-real-key"
"""
    ctx = {
        "patches": [
            {"filename": "app/main.py", "status": "modified", "patch": patch},
        ],
    }
    diff, _ = run_rules_diff(ctx)
    assert len(diff.all_atoms) == 1
    assert diff.all_atoms[0].file_path == "app/main.py"


def test_rules_review_detects_secret_in_patch():
    patch = """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
+password = "test-only-placeholder"
"""
    ctx = {
        "patches": [
            {"filename": "config.py", "status": "modified", "patch": patch},
        ],
    }
    diff, _ = run_rules_diff(ctx)
    review, hits, stats, _ = run_rules_review(diff, ctx)
    assert stats.pro_calls == 0
    assert stats.flash_calls == 0
    assert len(hits) >= 1
    assert len(review.risks) >= 1
    assert hits[0].line_start == 1
    assert hits[0].line_end == 1
    assert review.risks[0].line_start == 1


def test_locate_added_evidence_lines_across_hunks():
    patch = """@@ -2,2 +10,3 @@
 keep
+dangerous_call(user_input)
 old
@@ -20,1 +30,2 @@
+other_change()
+dangerous_call(second_input)
"""
    assert locate_added_evidence_lines(patch, "dangerous_call") == (11, 31)
