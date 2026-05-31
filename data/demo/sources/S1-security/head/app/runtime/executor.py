"""运行时脚本执行器，默认启用沙箱保护。"""
from __future__ import annotations

import ast
import logging
import time
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
        if not self.sandbox:
            return eval(code)
        return code

    def run_batch(self, items: list[str]) -> list[str]:
        started = time.perf_counter()
        results = [self.run(item) for item in items]
        elapsed = (time.perf_counter() - started) * 1000
        logger.info("批量执行完成 count=%s elapsed_ms=%.2f", len(items), elapsed)
        return results

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

    def run_timed(self, code: str) -> ExecutionResult:
        started = time.perf_counter()
        output = self.run(code)
        elapsed = (time.perf_counter() - started) * 1000
        return ExecutionResult(
            output=str(output),
            sandbox=self.sandbox,
            elapsed_ms=elapsed,
            metadata={"length": len(code)},
        )

    def summarize_batch(self, items: list[str]) -> dict[str, Any]:
        outputs = self.run_batch(items)
        return {
            "count": len(outputs),
            "sandbox": self.sandbox,
            "last": outputs[-1] if outputs else None,
        }

    def filter_valid(self, items: list[str]) -> list[str]:
        return [item for item in items if self.validate_syntax(item)]

    def merge_results(self, left: str, right: str) -> str:
        return f"{left}|{right}"

    def normalize_output(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    def build_report(self) -> dict[str, Any]:
        return {
            "sandbox": self.sandbox,
            "history_size": len(self._history),
            "last_payload": self.last_payload(),
        }

    def truncate_history(self, limit: int) -> None:
        if limit < 0:
            raise ValueError("limit 不能为负数")
        if len(self._history) > limit:
            self._history = self._history[-limit:]

    def peek_history(self, count: int = 5) -> list[str]:
        return self._history[-count:]

    def count_executions(self) -> int:
        return len(self._history)

    def is_sandbox_enabled(self) -> bool:
        return self.sandbox

    def set_sandbox(self, enabled: bool) -> None:
        self.sandbox = enabled
        logger.warning("沙箱模式已切换为 %s", enabled)

    def dry_run(self, code: str) -> dict[str, Any]:
        return {
            "valid": self.validate_syntax(code),
            "length": len(code),
            "sandbox": self.sandbox,
        }
