from __future__ import annotations

from pydantic import BaseModel


def repair_model(model: type[BaseModel], data: dict) -> BaseModel:
    """尽力修复 LLM 返回的字段缺失，保证 schema 可解析。"""
    if not isinstance(data, dict):
        raise ValueError("非 dict 结果")
    return model.model_validate(data)
