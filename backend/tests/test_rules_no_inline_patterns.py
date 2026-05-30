"""rules Python 模块不得内联业务 regex（规则仅在 YAML）。"""

from __future__ import annotations

import re
from pathlib import Path


def test_rules_python_modules_have_no_regex_literals():
    rules_dir = Path(__file__).resolve().parents[1] / "app" / "rules"
    pattern = re.compile(r're\.compile\s*\(\s*r["\']')
    for path in rules_dir.rglob("*.py"):
        if path.name in {"rule_evaluator.py", "rule_pattern.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), f"{path.name} 不得内联 re.compile 业务 pattern"
