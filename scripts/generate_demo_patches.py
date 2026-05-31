"""从 data/demo/sources 生成评委演示 Patch（产物为 data/demo/*.patch）。"""

from __future__ import annotations

import re
import sys
from difflib import unified_diff
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "data" / "demo"
SOURCES_DIR = DEMO_DIR / "sources"

sys.path.insert(0, str(REPO_ROOT / "backend"))
from app.local.demo_patch_stats import assert_demo_patch_thresholds, count_patch_stats  # noqa: E402

PLACEHOLDER_PATTERNS = (
    re.compile(r"extra_\d+"),
    re.compile(r"step_\d+"),
    re.compile(r"stable_block_"),
    re.compile(r"=\s*\w+\s+value\s+\d"),
    re.compile(r"(FEATURE|OPTION|SECRET|TAIL|auth_helper|boot_|line_|add_|grow_)_\d+"),
)

SCENARIOS: dict[str, str] = {
    "S1-security": "S1-security.patch",
    "S2-change-surface": "S2-change-surface.patch",
    "S3-governance": "S3-governance.patch",
}

EXPECTED_RULES: dict[str, set[str]] = {
    "S1-security": {"patch-hardcoded-secret", "eval-or-exec"},
    "S2-change-surface": {"dockerfile-changed", "dockerfile-root-user", "ci-config-changed"},
    "S3-governance": {"lockfile-changed", "requirements-unpinned", "test-file-removed"},
}


def _file_diff(path: str, old_text: str, new_text: str) -> str:
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    if old_lines and not old_lines[-1].endswith("\n"):
        old_lines[-1] += "\n"
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"
    body = list(
        unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        )
    )
    if not body:
        return ""
    header = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}"]
    rest = [line.rstrip("\n") for line in body[2:]]
    return "\n".join(header + rest) + "\n"


def _collect_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            files[rel] = path
    return files


def build_patch_from_sources(scenario_id: str) -> str:
    base_dir = SOURCES_DIR / scenario_id / "base"
    head_dir = SOURCES_DIR / scenario_id / "head"
    if not base_dir.is_dir() or not head_dir.is_dir():
        raise FileNotFoundError(f"缺少源码树: {base_dir} 或 {head_dir}")

    base_files = _collect_files(base_dir)
    head_files = _collect_files(head_dir)
    all_paths = sorted(set(base_files) | set(head_files))
    parts: list[str] = []
    for rel in all_paths:
        old_text = base_files[rel].read_text(encoding="utf-8") if rel in base_files else ""
        new_text = head_files[rel].read_text(encoding="utf-8") if rel in head_files else ""
        if old_text == new_text:
            continue
        chunk = _file_diff(rel, old_text, new_text)
        if chunk:
            parts.append(chunk)
    return "".join(parts)


def _assert_no_placeholders(text: str, label: str) -> None:
    for line in text.splitlines():
        if not line.startswith("+"):
            continue
        body = line[1:]
        for pattern in PLACEHOLDER_PATTERNS:
            assert not pattern.search(body), f"{label}: 占位行 {body[:80]!r}"


def _assert_realistic_added_lines(text: str, label: str) -> None:
    added = [ln[1:] for ln in text.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    signals = sum(
        1
        for ln in added
        if any(kw in ln for kw in ("def ", "class ", "import ", "assert ", "return ", "FROM ", "runs-on:"))
    )
    assert signals >= 20, f"{label}: 真实代码信号过少 ({signals})"


def _assert_rules(scenario_id: str, patch_text: str) -> None:
    from app.local.file_io import parse_patch_text
    from app.rules.pipeline.rules_diff import run_rules_diff
    from app.rules.pipeline.rules_review import run_rules_review

    patches = parse_patch_text(patch_text)
    ctx = {"patches": patches, "file_paths": [p["filename"] for p in patches]}
    diff, _ = run_rules_diff(ctx)
    _, hits, _, _ = run_rules_review(diff, ctx)
    hit_ids = {h.rule_id for h in hits}
    expected = EXPECTED_RULES[scenario_id]
    assert hit_ids == expected, f"{scenario_id}: hits {hit_ids} != expected {expected}"


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    for scenario_id, filename in SCENARIOS.items():
        content = build_patch_from_sources(scenario_id)
        assert content.strip(), f"{scenario_id}: 空 patch"
        _assert_no_placeholders(content, filename)
        _assert_realistic_added_lines(content, filename)
        stats = assert_demo_patch_thresholds(content, label=filename)
        _assert_rules(scenario_id, content)
        (DEMO_DIR / filename).write_text(content, encoding="utf-8")
        print(
            f"{filename}: files={stats['files']} +/-={stats['total']} "
            f"ge15={stats['files_ge_15']} multi_hunk={stats['multi_hunk_files']}"
        )
    print("Wrote demo patches to", DEMO_DIR)


if __name__ == "__main__":
    main()
