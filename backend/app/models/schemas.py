from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class InputType(str, Enum):
    PR_URL = "pr_url"
    PATCH = "patch"
    LOCAL_PATH = "local_path"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentProgress(BaseModel):
    agent_id: int = Field(ge=1, le=5)
    name: str
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    message: str = ""


class GraphNode(BaseModel):
    id: str
    label: str
    group: str = "default"
    risk: RiskLevel | None = None
    confidence: ConfidenceLevel | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class DiagramData(BaseModel):
    diagram_type: Literal["architecture", "impact_overlay", "path_compare"]
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    mermaid: str = ""


class ProjectIndexSchema(BaseModel):
    version: Literal["base", "head"] = "base"
    modules: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    entry_files: list[str] = Field(default_factory=list)
    flow_hints: list[str] = Field(default_factory=list)
    readme_excerpt: str = ""
    directory_tree: list[str] = Field(default_factory=list)
    code_snippets: dict[str, str] = Field(default_factory=dict)
    architecture_diagram: DiagramData | None = None
    raw_summary: str = ""


class DiffAtom(BaseModel):
    id: str
    file_path: str
    change_type: Literal["added", "modified", "removed", "renamed"]
    symbol: str = ""
    route_or_api: str = ""
    dependency_hint: str = ""
    summary: str = ""
    patch_excerpt: str = ""
    affected_symbols: list[str] = Field(default_factory=list)


class DiffCompareSchema(BaseModel):
    file_diffs: list[DiffAtom] = Field(default_factory=list)
    function_diffs: list[DiffAtom] = Field(default_factory=list)
    route_diffs: list[DiffAtom] = Field(default_factory=list)
    dependency_diffs: list[DiffAtom] = Field(default_factory=list)
    impact_diagram: DiagramData | None = None
    all_atoms: list[DiffAtom] = Field(default_factory=list)


class RiskItem(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    evidence: str = ""
    suggestion: str = ""
    related_atoms: list[str] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)


class MissingInfoItem(BaseModel):
    module: str
    reason: str
    suggestion: str = ""


class AtomContextPlan(BaseModel):
    atom_id: str
    diff_type: str = ""
    layer1_paths: list[str] = Field(default_factory=list)
    layer2_paths: list[str] = Field(default_factory=list)
    need_deeper: bool = False
    new_concerns: list[str] = Field(default_factory=list)


class AtomContextPlanBatch(BaseModel):
    plans: list[AtomContextPlan] = Field(default_factory=list)


class AtomPriorityBatch(BaseModel):
    ordered_atom_ids: list[str] = Field(default_factory=list)
    uncovered_reason: str = ""


class RiskReviewSchema(BaseModel):
    risks: list[RiskItem] = Field(default_factory=list)
    missing_info: list[MissingInfoItem] = Field(default_factory=list)
    degradation_notes: list[str] = Field(default_factory=list)


class VisualizationSchema(BaseModel):
    summary: str = ""
    summary_bullets: list[str] = Field(default_factory=list)
    diagrams: list[DiagramData] = Field(default_factory=list)
    detected_project_type: str = ""
    detected_framework: str = ""


class CompressStatsSchema(BaseModel):
    """混合模式本地压缩统计（字段名供 API/前端契约使用）。"""

    compress_calls: int = 0
    chars_before: int = 0
    chars_after: int = 0


class ReviewStats(BaseModel):
    review_depth_mode: str = "balanced"
    review_depth_label: str = ""
    total_atoms: int = 0
    reviewed_atoms: int = 0
    batches_run: int = 0
    pro_calls: int = 0
    flash_calls: int = 0


class TaskResultSchema(BaseModel):
    summary: str = ""
    summary_bullets: list[str] = Field(default_factory=list)
    diagrams: list[DiagramData] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    missing_info: list[MissingInfoItem] = Field(default_factory=list)
    degradation_notes: list[str] = Field(default_factory=list)
    diff_atoms: list[DiffAtom] = Field(default_factory=list)
    base_index: ProjectIndexSchema | None = None
    head_index: ProjectIndexSchema | None = None
    detected_project_type: str = ""
    detected_framework: str = ""
    review_stats: ReviewStats | None = None


class CreateTaskRequest(BaseModel):
    input_type: InputType
    value: str
    project_type: str | None = None
    framework: str | None = None
    review_depth_mode: str | None = None
    llm_mode: str | None = None
    local_compress_enabled: bool | None = None
    local_model: str | None = None
    cloud_flash_model: str | None = None
    cloud_pro_model: str | None = None

    @field_validator("value")
    @classmethod
    def value_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("输入内容不能为空")
        return v.strip()


class RerunRequest(BaseModel):
    extra_context_paths: list[str] = Field(default_factory=list, max_length=10)
    focus_atom_ids: list[str] = Field(default_factory=list, max_length=3)

    @field_validator("focus_atom_ids")
    @classmethod
    def max_focus(cls, v: list[str]) -> list[str]:
        if len(v) > 3:
            raise ValueError("重点复审差异点最多 3 个")
        return v


class TaskRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    input_type: InputType
    input_value: str
    status: TaskStatus = TaskStatus.PENDING
    current_agent: int = 0
    agent_progress: list[AgentProgress] = Field(default_factory=list)
    project_type: str | None = None
    framework: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: str | None = None
    rerun_used: bool = False
    rerun_context_paths: list[str] = Field(default_factory=list)
    rerun_focus_atoms: list[str] = Field(default_factory=list)
    review_depth_mode: str = "balanced"
    review_depth_label: str = ""
    llm_mode: str = "cloud_only"
    llm_mode_label: str = ""
    local_compress_enabled: bool = False
    local_model: str = ""
    cloud_flash_model: str = ""
    cloud_pro_model: str = ""
    compress_stats: CompressStatsSchema | None = None
    result: TaskResultSchema | None = None
    pr_context: dict[str, Any] = Field(default_factory=dict)

    def init_agent_progress(self) -> None:
        names = [
            "原版本扫描",
            "PR 版本扫描",
            "差异对比",
            "递进式审阅",
            "可视化组织",
        ]
        self.agent_progress = [
            AgentProgress(agent_id=i + 1, name=names[i], status="pending") for i in range(5)
        ]
