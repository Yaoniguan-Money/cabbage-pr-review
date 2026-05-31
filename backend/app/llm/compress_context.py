"""混合模式输入压缩：仅输出纯文本，不产出业务结论。"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.llm.ollama_provider import OllamaProvider
from app.llm.task_context import TaskLLMContext, get_task_llm_context
from app.local.text_preprocess import truncate

logger = logging.getLogger(__name__)

_COMPRESS_SYSTEM = (
    "你是代码上下文压缩助手。任务：缩短输入文本，保留结构信号。"
    "规则：只删不改、不推断风险、不编造代码；保留 import、类/函数签名、路由、配置项、与变更相关的逻辑。"
    "输出纯文本摘要，不要 JSON，不要 markdown 代码块。"
)


@dataclass
class CompressStats:
    compress_calls: int = 0
    chars_before: int = 0
    chars_after: int = 0


_compress_stats: CompressStats = CompressStats()
_compress_degradation_notes: list[str] = []
_ollama = OllamaProvider()


def reset_compress_stats() -> None:
    global _compress_stats, _compress_degradation_notes
    _compress_stats = CompressStats()
    _compress_degradation_notes = []


def get_compress_stats() -> CompressStats:
    return _compress_stats


def get_compress_degradation_notes() -> list[str]:
    return list(_compress_degradation_notes)


def should_compress_file(
    path: str,
    *,
    changed_paths: set[str],
    entry_files: set[str],
) -> bool:
    norm = path.replace("\\", "/")
    if norm in changed_paths or norm in entry_files:
        return False
    return True


def compress_text(content: str, *, path: str, ctx: TaskLLMContext | None = None) -> str:
    """压缩单文件文本；失败时回退 truncate。"""
    task_ctx = ctx or get_task_llm_context()
    if not task_ctx.local_compress_enabled or task_ctx.llm_mode != "hybrid":
        return content
    if not task_ctx.local_model:
        return content
    if len(content) <= 2000:
        return content
    global _compress_stats
    _compress_stats.chars_before += len(content)
    try:
        user_msg = f"文件路径: {path}\n\n---\n{truncate(content, 12000)}"
        summary = _ollama.complete_text_sync(
            model=task_ctx.local_model,
            system=_COMPRESS_SYSTEM,
            user=user_msg,
            tier="local_compress",
        )
        out = summary.strip() or content
        _compress_stats.compress_calls += 1
        _compress_stats.chars_after += len(out)
        return out
    except Exception as e:
        logger.warning("压缩失败 %s: %s，回退 truncate", path, e)
        global _compress_degradation_notes
        _compress_degradation_notes.append(f"本地压缩降级 {path}: {e}，已回退 truncate")
        out = truncate(content, 8000)
        _compress_stats.chars_after += len(out)
        return out


def compress_file_map(
    files: dict[str, str],
    *,
    changed_paths: set[str] | None = None,
    entry_files: set[str] | None = None,
    ctx: TaskLLMContext | None = None,
) -> dict[str, str]:
    task_ctx = ctx or get_task_llm_context()
    if not task_ctx.local_compress_enabled or task_ctx.llm_mode != "hybrid":
        return dict(files)
    changed = changed_paths or set()
    entries = entry_files or set()
    out: dict[str, str] = {}
    for path, text in files.items():
        if should_compress_file(path, changed_paths=changed, entry_files=entries):
            out[path] = compress_text(text, path=path, ctx=task_ctx)
        else:
            out[path] = text
    return out
