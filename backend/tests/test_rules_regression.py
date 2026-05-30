"""默认规则包逐条回归：命中/不命中用例均在 YAML 驱动，Python 仅做通用断言。"""

from __future__ import annotations

import pytest

from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review
from app.rules.rule_loader import lint_rules, load_rule_pack


def _patch_ctx(filename: str, patch: str, *, status: str = "modified") -> dict:
    return {
        "patches": [{"filename": filename, "status": status, "patch": patch}],
    }


def _run_hits(ctx: dict) -> set[str]:
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    return {hit.rule_id for hit in hits}


def test_default_pack_lint_clean():
    rules, config = load_rule_pack()
    assert lint_rules(rules, pack_config=config) == []


@pytest.mark.parametrize(
    ("ctx", "expected_rule"),
    [
        (
            _patch_ctx(
                "config.py",
                "@@ -1,2 +1,3 @@\n+password = \"hardcoded123456\"\n",
            ),
            "patch-hardcoded-secret",
        ),
        (
            _patch_ctx(".env", "", status="added"),
            "env-file-committed",
        ),
        (
            _patch_ctx(
                "db.py",
                "@@ -1,2 +1,3 @@\n+cursor.execute(\"SELECT \" + user_input)\n",
            ),
            "sql-string-concat",
        ),
        (
            _patch_ctx(
                "run.py",
                "@@ -1,2 +1,3 @@\n+eval(user_code)\n",
            ),
            "eval-or-exec",
        ),
        (
            _patch_ctx(
                "ui.tsx",
                "@@ -1,2 +1,3 @@\n+<div dangerouslySetInnerHTML={{__html: html}} />\n",
            ),
            "dangerous-html-react",
        ),
        (
            _patch_ctx(
                "app/main.py",
                "@@ -1,2 +1,5 @@\n+@app.get(\"/users\")\n+def users():\n+    pass\n",
            ),
            "route-decorator-changed",
        ),
        (
            _patch_ctx(
                "app/middleware/auth.py",
                "@@ -1,2 +1,3 @@\n+def authenticate(request):\n",
            ),
            "auth-middleware-touched",
        ),
        (
            _patch_ctx(".github/workflows/ci.yml", "@@ -1 +1 @@\n-x\n+y\n"),
            "ci-config-changed",
        ),
        (
            _patch_ctx("Dockerfile", "@@ -1 +1 @@\n-FROM node:18\n+FROM node:20\n"),
            "dockerfile-changed",
        ),
        (
            _patch_ctx("package-lock.json", "@@ -1 +1 @@\n-old\n+new\n"),
            "lockfile-changed",
        ),
        (
            _patch_ctx(
                "requirements.txt",
                "@@ -1,2 +1,3 @@\n+requests\n",
            ),
            "requirements-unpinned",
        ),
    ],
)
def test_rule_positive_hit(ctx: dict, expected_rule: str):
    hits = _run_hits(ctx)
    assert expected_rule in hits


@pytest.mark.parametrize(
    ("ctx", "unexpected_rule"),
    [
        (
            _patch_ctx(
                "config.py",
                "@@ -1,2 +1,3 @@\n+USER_NAME = \"admin\"\n",
            ),
            "patch-hardcoded-secret",
        ),
        (
            _patch_ctx(
                "requirements.txt",
                "@@ -1,2 +1,3 @@\n+requests==2.31.0\n",
            ),
            "requirements-unpinned",
        ),
        (
            _patch_ctx(
                "app/utils.py",
                "@@ -1,2 +1,3 @@\n+# session helper\n",
            ),
            "auth-middleware-touched",
        ),
    ],
)
def test_rule_negative_no_hit(ctx: dict, unexpected_rule: str):
    hits = _run_hits(ctx)
    assert unexpected_rule not in hits


def test_large_patch_hunk_threshold():
    added = "\n".join(f"+line_{i}" for i in range(105))
    patch = f"@@ -1,1 +1,106 @@\n{added}\n"
    ctx = _patch_ctx("big.py", patch)
    hits = _run_hits(ctx)
    assert "large-patch-hunk" in hits


def test_large_patch_hunk_below_threshold_no_hit():
    added = "\n".join(f"+line_{i}" for i in range(55))
    patch = f"@@ -1,1 +1,56 @@\n{added}\n"
    ctx = _patch_ctx("big.py", patch)
    hits = _run_hits(ctx)
    assert "large-patch-hunk" not in hits


def test_test_file_removed_threshold():
    removed = "\n".join(f"-assert i == {i}" for i in range(12))
    patch = f"@@ -1,13 +1,1 @@\n{removed}\n"
    ctx = _patch_ctx("tests/test_api.py", patch)
    hits = _run_hits(ctx)
    assert "test-file-removed" in hits


def test_test_file_removed_no_hit_on_minor_test_edit():
    """+85/-1 场景不应误报 test-file-removed。"""
    added = "\n".join(f"+line_{i}" for i in range(85))
    patch = f"@@ -1,2 +1,87 @@\n{added}\n-one line\n"
    ctx = _patch_ctx("backend/tests/test_llm_mode.py", patch)
    hits = _run_hits(ctx)
    assert "test-file-removed" not in hits


def test_risks_grouped_by_rule_id():
    added = "\n".join(f"+line_{i}" for i in range(105))
    patch = f"@@ -1,1 +1,106 @@\n{added}\n"
    ctx = {
        "patches": [
            {"filename": "a/big.py", "status": "modified", "patch": patch},
            {"filename": "b/big.py", "status": "modified", "patch": patch},
        ],
    }
    diff, _ = run_rules_diff(ctx)
    review, hits, _, _ = run_rules_review(diff, ctx)
    large_hits = [h for h in hits if h.rule_id == "large-patch-hunk"]
    assert len(large_hits) >= 2
    large_risks = [r for r in review.risks if "变更行数较多" in r.title]
    assert len(large_risks) == 1
    assert len(large_risks[0].file_paths or []) >= 2


def test_dockerfile_root_user_match_all():
    ctx = {
        "patches": [
            {
                "filename": "Dockerfile",
                "status": "modified",
                "patch": "@@ -1,2 +1,3 @@\n+USER root\n",
            }
        ],
    }
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    assert any(h.rule_id == "dockerfile-root-user" for h in hits)


def test_metadata_suggestion_from_yaml():
    ctx = _patch_ctx(
        "config.py",
        "@@ -1,2 +1,3 @@\n+password = \"hardcoded123456\"\n",
    )
    diff, _ = run_rules_diff(ctx)
    review, hits, _, _ = run_rules_review(diff, ctx)
    assert any(h.rule_id == "patch-hardcoded-secret" for h in hits)
    secret_risks = [r for r in review.risks if "硬编码" in r.title]
    assert secret_risks
    assert "环境变量" in secret_risks[0].suggestion
