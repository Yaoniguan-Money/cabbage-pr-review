from __future__ import annotations

from app.llm.compress_context import (
    compress_file_map,
    get_compress_degradation_notes,
    get_compress_stats,
    reset_compress_stats,
    should_compress_file,
)
from app.llm.task_context import TaskLLMContext, set_task_llm_context, clear_task_llm_context


def test_should_compress_file_skips_changed_and_entry():
    changed = {"src/a.py"}
    entries = {"main.py"}
    assert should_compress_file("src/a.py", changed_paths=changed, entry_files=entries) is False
    assert should_compress_file("main.py", changed_paths=changed, entry_files=entries) is False
    assert should_compress_file("lib/util.py", changed_paths=changed, entry_files=entries) is True


def test_compress_file_map_off_when_not_hybrid():
    clear_task_llm_context()
    set_task_llm_context(
        TaskLLMContext(
            llm_mode="cloud_only",
            local_compress_enabled=True,
            local_model="m",
            cloud_flash_model="f",
            cloud_pro_model="p",
        )
    )
    files = {"lib/x.py": "x" * 5000}
    out = compress_file_map(files, changed_paths=set(), entry_files=set())
    assert out == files


def test_compress_file_map_hybrid_without_ollama_fallback(monkeypatch):
    clear_task_llm_context()
    reset_compress_stats()
    set_task_llm_context(
        TaskLLMContext(
            llm_mode="hybrid",
            local_compress_enabled=True,
            local_model="m",
            cloud_flash_model="f",
            cloud_pro_model="p",
        )
    )

    def boom(**kwargs):
        raise RuntimeError("no ollama")

    monkeypatch.setattr("app.llm.compress_context._ollama.complete_text_sync", boom)
    files = {"lib/x.py": "y" * 3000}
    out = compress_file_map(files, changed_paths=set(), entry_files=set())
    assert "lib/x.py" in out
    assert len(out["lib/x.py"]) <= 8000
    notes = get_compress_degradation_notes()
    assert len(notes) == 1
    assert "本地压缩降级" in notes[0]
    stats = get_compress_stats()
    assert stats.chars_before > 0
