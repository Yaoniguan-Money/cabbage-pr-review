"""Phase 2：hunk 级 DiffAtom 拆分测试。"""

from __future__ import annotations

from app.rules.pipeline.rules_diff import run_rules_diff


def _ctx(filename: str, patch: str) -> dict:
    return {"patches": [{"filename": filename, "status": "modified", "patch": patch}]}


def test_single_hunk_still_one_atom():
    patch = """@@ -1,2 +1,3 @@
+password = "hardcoded123456"
"""
    diff, _ = run_rules_diff(_ctx("config.py", patch))
    assert len(diff.all_atoms) == 1
    assert diff.all_atoms[0].hunk_patch == ""


def test_multi_hunk_splits_into_atoms():
    patch = """@@ -1,2 +1,3 @@
+line_a = 1
@@ -10,2 +11,3 @@
+line_b = 2
"""
    diff, notes = run_rules_diff(_ctx("app/service.py", patch))
    assert len(diff.all_atoms) == 2
    assert diff.all_atoms[0].symbol == "hunk:1"
    assert diff.all_atoms[1].symbol == "hunk:2"
    assert diff.all_atoms[0].hunk_patch.startswith("@@")
    assert "line_a" in diff.all_atoms[0].patch_excerpt
    assert "line_b" in diff.all_atoms[1].patch_excerpt
    assert not notes


def test_hunk_atom_scoped_regex_hit():
    """仅第二个 hunk 含 eval，应对该 hunk atom 命中而非整文件合并。"""
    from app.rules.pipeline.rules_review import run_rules_review

    patch = """@@ -1,2 +1,3 @@
+# safe comment
@@ -5,2 +6,3 @@
+eval(user_code)
"""
    ctx = _ctx("run.py", patch)
    diff, _ = run_rules_diff(ctx)
    assert len(diff.all_atoms) == 2
    _, hits, _, _ = run_rules_review(diff, ctx)
    eval_hits = [h for h in hits if h.rule_id == "eval-or-exec"]
    assert len(eval_hits) == 1
    assert eval_hits[0].file_path == "run.py"


def test_split_can_be_disabled():
    patch = """@@ -1,2 +1,3 @@
+a
@@ -4,2 +5,3 @@
+b
"""
    diff, _ = run_rules_diff(_ctx("x.py", patch), split_patch_hunks=False)
    assert len(diff.all_atoms) == 1
