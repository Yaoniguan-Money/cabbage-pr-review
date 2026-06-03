"""混合模式输入压缩：仅输出纯文本，不产出业务结论。"""

from __future__ import annotations

import logging
import threading
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


# per-task dict 隔离，避免 ThreadPoolExecutor 多线程竞态
_stats: dict[str, CompressStats] = {}
_degradation_notes: dict[str, list[str]] = {}
_lock = threading.Lock()
_ollama = OllamaProvider()


_DEFAULT_TASK = "_default"


def _current_task_id() -> str:
    from app.services.task_progress import _task_id_ctx

    return _task_id_ctx.get() or _DEFAULT_TASK


def _get_stats(task_id: str = "") -> CompressStats:
    tid = task_id or _current_task_id()
    with _lock:
        if tid not in _stats:
            _stats[tid] = CompressStats()
        return _stats[tid]


def _get_notes(task_id: str = "") -> list[str]:
    tid = task_id or _current_task_id()
    with _lock:
        if tid not in _degradation_notes:
            _degradation_notes[tid] = []
        return _degradation_notes[tid]


def reset_compress_stats(task_id: str = "") -> None:
    tid = task_id or _current_task_id()
    if not tid:
        return
    with _lock:
        _stats[tid] = CompressStats()
        _degradation_notes[tid] = []


def get_compress_stats(task_id: str = "") -> CompressStats:
    tid = task_id or _current_task_id()
    with _lock:
        return _stats.get(tid, CompressStats())


def get_compress_degradation_notes(task_id: str = "") -> list[str]:
    tid = task_id or _current_task_id()
    with _lock:
        return list(_degradation_notes.get(tid, []))


def cleanup_compress_stats(task_id: str) -> None:
    """任务结束后清理，防止内存泄漏。"""
    with _lock:
        _stats.pop(task_id, None)
        _degradation_notes.pop(task_id, None)


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
    stats = _get_stats()
    stats.chars_before += len(content)
    try:
        user_msg = f"文件路径: {path}\n\n---\n{truncate(content, 12000)}"
        summary = _ollama.complete_text_sync(
            model=task_ctx.local_model,
            system=_COMPRESS_SYSTEM,
            user=user_msg,
            tier="local_compress",
        )
        out = summary.strip() or content
        stats.compress_calls += 1
        stats.chars_after += len(out)
        return out
    except Exception as e:
        logger.warning("压缩失败 %s: %s，回退 truncate", path, e)
        notes = _get_notes()
        notes.append(f"本地压缩降级 {path}: {e}，已回退 truncate")
        out = truncate(content, 8000)
        stats.chars_after += len(out)
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
