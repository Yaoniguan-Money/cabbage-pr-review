"""Tree-sitter AST 求值插件（业务 query 仅存在于 YAML）。"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.rules.rule_loader import infer_language

logger = logging.getLogger(__name__)

_AST_AVAILABLE: bool | None = None


def ast_engine_available() -> bool:
    global _AST_AVAILABLE
    if _AST_AVAILABLE is None:
        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_python  # noqa: F401

            _AST_AVAILABLE = True
        except ImportError:
            _AST_AVAILABLE = False
    return _AST_AVAILABLE


@lru_cache(maxsize=8)
def _language_for(lang: str) -> Any | None:
    try:
        from tree_sitter import Language
    except ImportError:
        return None

    key = lang.lower()
    if key == "python":
        import tree_sitter_python as tspython

        return Language(tspython.language())
    if key in {"javascript", "typescript"}:
        try:
            import tree_sitter_javascript as tsjs
        except ImportError:
            return None
        return Language(tsjs.language())
    return None


def _source_for_ast(file_path: str, source: str) -> str:
    """将 diff 新增行拼成可解析片段（必要时包一层函数并缩进）。"""
    text = source.strip()
    if not text:
        return ""
    if infer_language(file_path) == "python":
        lines = text.splitlines()
        if not lines:
            return ""
        body = "\n".join(f"    {line}" if line.strip() else line for line in lines)
        return f"def __rule_patch_fn__():\n{body}\n"
    return text


def _child_types(node: Any) -> set[str]:
    return {child.type for child in node.children}


def _passes_ast_filter(node: Any, ast_filter: str) -> bool:
    if not ast_filter:
        return True
    if ast_filter == "bare_except":
        if node.type != "except_clause":
            return False
        return "identifier" not in _child_types(node)
    if ast_filter == "wildcard_import":
        return node.type == "import_from_statement" and "wildcard_import" in _child_types(node)
    return True


def run_ast_query(
    *,
    file_path: str,
    source: str,
    query_text: str,
    ast_filter: str = "",
) -> str | None:
    """对源码片段执行 tree-sitter query；命中返回证据摘要。"""
    if not ast_engine_available() or not query_text.strip():
        return None

    lang = infer_language(file_path)
    language = _language_for(lang)
    if language is None:
        return None

    wrapped = _source_for_ast(file_path, source)
    if not wrapped:
        return None

    try:
        from tree_sitter import Parser, Query, QueryCursor
    except ImportError:
        return None

    try:
        parser = Parser(language)
        tree = parser.parse(wrapped.encode("utf-8"))
        query = Query(language, query_text)
        cursor = QueryCursor(query)
    except Exception as exc:
        logger.debug("AST 解析失败 %s: %s", file_path, exc)
        return None

    snippets: list[str] = []
    try:
        for _pattern_index, capture_map in cursor.matches(tree.root_node):
            for _name, nodes in capture_map.items():
                for node in nodes:
                    if not _passes_ast_filter(node, ast_filter):
                        continue
                    snippet = wrapped.encode("utf-8")[node.start_byte : node.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    snippet = snippet.strip()
                    if snippet and snippet not in snippets:
                        snippets.append(snippet[:200])
                    if len(snippets) >= 3:
                        break
                if len(snippets) >= 3:
                    break
            if len(snippets) >= 3:
                break
    except Exception as exc:
        logger.debug("AST query 失败 %s: %s", file_path, exc)
        return None

    if not snippets:
        return None
    return snippets[0] if len(snippets) == 1 else " | ".join(snippets)
