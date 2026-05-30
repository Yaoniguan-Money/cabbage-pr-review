"""从配置目录加载 YAML 规则包与索引提示。"""

from __future__ import annotations

import os
from fnmatch import fnmatch
from pathlib import Path

import yaml

from app.rules.rule_schema import IndexHintsDocument, RuleDefinition, RulePackConfig, RulePackDocument

_RULES_MODULE_DIR = Path(__file__).resolve().parent
_DEFAULT_PACK_DIR = _RULES_MODULE_DIR / "packs" / "default"
# 兼容旧路径 backend/rules/default（本地开发迁移前）
_LEGACY_PACK_DIR = _RULES_MODULE_DIR.parents[2] / "rules" / "default"


def resolve_rules_pack_dir() -> Path:
    override = (os.environ.get("RULES_PACK_PATH") or "").strip()
    if override:
        path = Path(override)
        if path.is_dir():
            return path
    from app.config import settings

    if settings.rules_pack_path.strip():
        path = Path(settings.rules_pack_path)
        if path.is_dir():
            return path
    if _DEFAULT_PACK_DIR.is_dir():
        return _DEFAULT_PACK_DIR
    return _LEGACY_PACK_DIR


def _load_yaml(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {}


def load_index_hints(pack_dir: Path | None = None) -> list[str]:
    directory = pack_dir or resolve_rules_pack_dir()
    hints_path = directory / "index_hints.yaml"
    if not hints_path.is_file():
        return []
    doc = IndexHintsDocument.model_validate(_load_yaml(hints_path))
    return list(doc.entry_hints)


def load_rule_pack(pack_dir: Path | None = None) -> tuple[list[RuleDefinition], RulePackConfig]:
    directory = pack_dir or resolve_rules_pack_dir()
    if not directory.is_dir():
        return [], RulePackConfig()

    merged_rules: list[RuleDefinition] = []
    merged_config = RulePackConfig()

    for path in sorted(directory.glob("*.yaml")):
        if path.name in {"index_hints.yaml", "config.yaml"}:
            continue
        data = _load_yaml(path)
        doc = RulePackDocument.model_validate(data)
        merged_rules.extend(doc.rules)

    config_path = directory / "config.yaml"
    if config_path.is_file():
        cfg_doc = RulePackDocument.model_validate(_load_yaml(config_path))
        if cfg_doc.config is not None:
            merged_config = cfg_doc.config

    return merged_rules, merged_config


def path_matches_glob(file_path: str, patterns: list[str]) -> bool:
    normalized = file_path.replace("\\", "/")
    if not patterns:
        return True
    for pattern in patterns:
        if pattern in {"**/*", "*", "**"}:
            return True
        if fnmatch(normalized, pattern):
            return True
        bare = pattern.removeprefix("**/")
        if bare != pattern and fnmatch(normalized, bare):
            return True
    return False


def file_in_rule_scope(file_path: str, rule: RuleDefinition) -> bool:
    normalized = file_path.replace("\\", "/")
    if rule.paths.exclude and any(
        path_matches_glob(normalized, [pattern]) for pattern in rule.paths.exclude
    ):
        return False
    includes = rule.paths.include or ["**/*"]
    return any(path_matches_glob(normalized, [pattern]) for pattern in includes)


def infer_language(file_path: str) -> str:
    lower = file_path.lower()
    if lower.endswith(".py"):
        return "python"
    if lower.endswith((".ts", ".tsx")):
        return "typescript"
    if lower.endswith((".js", ".jsx")):
        return "javascript"
    if lower.endswith((".yaml", ".yml")):
        return "yaml"
    if lower.endswith(".json"):
        return "json"
    if lower.endswith((".md", ".toml", ".env", ".ini", ".cfg")):
        return "config"
    if "dockerfile" in lower:
        return "docker"
    return "unknown"


def language_allowed(file_path: str, languages: list[str]) -> bool:
    if not languages:
        return True
    lang = infer_language(file_path)
    normalized = {item.lower() for item in languages}
    if lang in normalized:
        return True
    if "config" in normalized and lang in {"yaml", "json", "config", "docker"}:
        return True
    return False
