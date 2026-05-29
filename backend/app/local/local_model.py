"""本地模型统一接口预留（v2.0 §7.4：首发不绑定具体本地模型）。"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LocalModelClient:
    def available(self) -> bool:
        return False

    def complete_json(self, prompt: str, schema: type[T]) -> T:
        raise NotImplementedError("本地模型未接入，请使用 DeepSeek 或启发式降级")


local_model_client = LocalModelClient()
