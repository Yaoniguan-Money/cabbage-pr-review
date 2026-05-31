import { useState, type ReactNode } from "react";

import type { TaskRecord } from "../api/client";
import AgentProgressBar from "./AgentProgressBar";
import { formatTemplate } from "../utils/formatTemplate";

interface ReviewHeaderProps {
  task: TaskRecord;
  taskId: string;
  ui: Record<string, string>;
  statusLabel: string;
  metaExtra?: ReactNode;
}

export default function ReviewHeader({
  task,
  taskId,
  ui,
  statusLabel,
  metaExtra,
}: ReviewHeaderProps) {
  const [showTaskId, setShowTaskId] = useState(false);
  const ctx = task.pr_context;
  const title = ctx?.title?.trim() || task.input_value;
  const branchLabel =
    ctx?.base_ref && ctx?.head_ref
      ? `${ctx.head_ref} ${formatTemplate(ui.branch_into, { ref: ctx.base_ref })}`
      : null;

  return (
    <header className="review-header">
      <div className="review-header-top">
        <span className={`status-badge status-${task.status}`}>{statusLabel}</span>
        <span className="meta-chip">
          {ui.meta_llm_mode}：{task.llm_mode_label || task.llm_mode || "—"}
        </span>
        <span className="meta-chip">
          {ui.meta_review_depth}：{task.review_depth_label || task.review_depth_mode || "—"}
        </span>
        {branchLabel ? <span className="meta-chip meta-chip-muted">{branchLabel}</span> : null}
        {ctx?.html_url ? (
          <a href={ctx.html_url} target="_blank" rel="noreferrer" className="review-external-link">
            {ui.open_pr_link}
          </a>
        ) : null}
        {metaExtra}
      </div>
      <h1 className="review-title">{title}</h1>
      <div className="review-task-id-row">
        <button
          type="button"
          className="secondary btn-chip task-id-toggle"
          onClick={() => setShowTaskId((v) => !v)}
        >
          {showTaskId ? ui.task_id_toggle_hide : ui.task_id_toggle_show}
        </button>
        {showTaskId ? (
          <p className="task-id">
            {ui.task_id_label}: {taskId}
          </p>
        ) : null}
      </div>
      <AgentProgressBar
        progress={task.agent_progress}
        stepperLabel={ui.agent_stepper_label}
        parallelLaneAria={ui.agent_parallel_lane_aria}
      />
    </header>
  );
}
