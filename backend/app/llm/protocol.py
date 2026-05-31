from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """LLM 后端协议：模型名由调用方传入，Provider 内不得写死。"""

    def available(self) -> bool: ...

    def complete_json_sync(self, *, model: str, system: str, user: str) -> dict: ...

    def list_models(self) -> list[str]: ...
