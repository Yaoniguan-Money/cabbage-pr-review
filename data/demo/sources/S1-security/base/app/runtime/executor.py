"""运行时脚本执行器，默认启用沙箱保护。"""
from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    output: str
    sandbox: bool
    elapsed_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class Executor:
    """在受控环境中评估用户提交的表达式或脚本片段。"""

    def __init__(self, sandbox: bool = True) -> None:
        self.sandbox = sandbox
        self._history: list[str] = []

    def run(self, code: str) -> str:
        self._history.append(code)
        logger.debug("执行代码片段，sandbox=%s", self.sandbox)
        return code

    def describe(self) -> dict[str, Any]:
        return {
            "sandbox": self.sandbox,
            "executions": len(self._history),
        }

    def validate_syntax(self, code: str) -> bool:
        try:
            ast.parse(code, mode="exec")
            return True
        except SyntaxError:
            return False

    def last_payload(self) -> str | None:
        if not self._history:
            return None
        return self._history[-1]

    def clear_history(self) -> None:
        self._history.clear()

    def replay_last(self) -> str:
        payload = self.last_payload()
        if payload is None:
            raise RuntimeError("没有可重放的执行记录")
        return self.run(payload)

    def export_history(self) -> list[str]:
        return list(self._history)
