"""规则 YAML 结构校验与严重级别映射。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.schemas import ConfidenceLevel, RiskLevel

MatchTarget = Literal[
    "patch_hunk",
    "file_path",
    "diff_atom",
    "change_type",
    "removed_lines",
    "pr_title",
    "pr_body",
]
PatchScope = Literal["added_only", "removed_only", "full_patch"]
MatcherType = Literal["regex", "ast"]
AstFilter = Literal["", "bare_except", "wildcard_import"]


class RulePathFilter(BaseModel):
    include: list[str] = Field(default_factory=lambda: ["**/*"])
    exclude: list[str] = Field(default_factory=list)


class RuleMatchClause(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pattern_regex: str = Field(default="", alias="pattern-regex")
    matcher_type: MatcherType = Field(default="regex", alias="matcher-type")
    ast_query: str = Field(default="", alias="ast-query")
    ast_filter: str = Field(default="", alias="ast-filter")
    target: MatchTarget = "patch_hunk"
    patch_scope: PatchScope = "added_only"


class RuleMatchGroup(BaseModel):
    any: list[RuleMatchClause] = Field(default_factory=list)
    all: list[RuleMatchClause] = Field(default_factory=list)


class RuleDefinition(BaseModel):
    id: str
    message: str
    severity: str = "MEDIUM"
    languages: list[str] = Field(default_factory=list)
    paths: RulePathFilter = Field(default_factory=RulePathFilter)
    match: RuleMatchGroup = Field(default_factory=RuleMatchGroup)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("规则 id 不能为空")
        return v.strip()


class RulePackScope(BaseModel):
    ignore_path_patterns: list[str] = Field(default_factory=list)
    max_atoms_per_run: int = 200
    split_patch_hunks: bool = True


class RulePackReporting(BaseModel):
    group_risks_by_rule_id: bool = True
    max_files_listed_per_risk: int = 15
    evidence_include_atom_summary: bool = True
    grouped_evidence_suffix: str = "等共 {count} 个文件"


class RulePackConfig(BaseModel):
    scope: RulePackScope = Field(default_factory=RulePackScope)
    metadata_allowed_keys: list[str] = Field(default_factory=list)
    reporting: RulePackReporting = Field(default_factory=RulePackReporting)


class RulePackDocument(BaseModel):
    rules: list[RuleDefinition] = Field(default_factory=list)
    config: RulePackConfig | None = None


class IndexHintsDocument(BaseModel):
    entry_hints: list[str] = Field(default_factory=list)


class RuleHitRecord(BaseModel):
    rule_id: str
    severity: str
    file_path: str
    evidence: str
    message: str
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)


_SEVERITY_TO_RISK: dict[str, RiskLevel] = {
    "CRITICAL": RiskLevel.HIGH,
    "HIGH": RiskLevel.HIGH,
    "ERROR": RiskLevel.HIGH,
    "MEDIUM": RiskLevel.MEDIUM,
    "WARNING": RiskLevel.MEDIUM,
    "LOW": RiskLevel.LOW,
    "INFO": RiskLevel.LOW,
}


def map_severity(severity: str) -> RiskLevel:
    key = (severity or "MEDIUM").upper()
    return _SEVERITY_TO_RISK.get(key, RiskLevel.MEDIUM)


def default_confidence_for_risk(level: RiskLevel) -> ConfidenceLevel:
    if level == RiskLevel.HIGH:
        return ConfidenceLevel.HIGH
    if level == RiskLevel.MEDIUM:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
