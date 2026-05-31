"""规则 pattern 编译（通用引擎，不含业务 regex）。"""

from __future__ import annotations

import re


def compile_pattern(pattern: str) -> re.Pattern[str] | None:
    if not pattern.strip():
        return None
    try:
        return re.compile(pattern, re.MULTILINE)
    except re.error:
        return None
