"""规则 YAML 结构校验与严重级别映射。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.schemas import ConfidenceLevel, RiskLevel

MatchTarget = Literal["patch_hunk", "file_path", "diff_atom"]


class RulePathFilter(BaseModel):
    include: list[str] = Field(default_factory=lambda: ["**/*"])
    exclude: list[str] = Field(default_factory=list)


class RuleMatchClause(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pattern_regex: str = Field(default="", alias="pattern-regex")
    target: MatchTarget = "patch_hunk"


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


class RulePackConfig(BaseModel):
    scope: RulePackScope = Field(default_factory=RulePackScope)


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
