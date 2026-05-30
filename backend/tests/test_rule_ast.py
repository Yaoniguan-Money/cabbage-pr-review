"""Phase 2：Tree-sitter AST 规则插件测试。"""

from __future__ import annotations

import pytest

from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review
from app.rules.rule_ast import ast_engine_available


pytestmark = pytest.mark.skipif(not ast_engine_available(), reason="tree-sitter 未安装")


def _run(rule_id: str, filename: str, patch: str) -> bool:
    ctx = {"patches": [{"filename": filename, "status": "modified", "patch": patch}]}
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    return any(h.rule_id == rule_id for h in hits)


def test_python_bare_except_ast_rule():
    patch = """@@ -1,2 +1,6 @@
+try:
+    risky()
+except:
+    pass
"""
    assert _run("python-bare-except", "app/handler.py", patch)


def test_python_wildcard_import_ast_rule():
    patch = """@@ -1,1 +1,2 @@
+from utils import *
"""
    assert _run("python-wildcard-import", "app/views.py", patch)


def test_ast_rule_no_false_positive_on_typed_except():
    patch = """@@ -1,1 +1,4 @@
+try:
+    risky()
+except ValueError:
+    pass
"""
    assert not _run("python-bare-except", "app/handler.py", patch)
