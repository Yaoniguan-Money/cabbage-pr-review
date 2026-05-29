from __future__ import annotations


def truncate(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n... [已截断]"


def clean_patch_lines(patch: str) -> str:
    return truncate(patch.replace("\r\n", "\n"), 8000)
