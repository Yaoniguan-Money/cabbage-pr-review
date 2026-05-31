import type { TaskResult } from "../api/client";
import { formatTemplate } from "../utils/formatTemplate";

export default function SummaryBar({
  result,
  ui,
  compact = false,
}: {
  result: TaskResult;
  ui: Record<string, string>;
  compact?: boolean;
}) {
  return (
    <div className={`summary-bar ${compact ? "summary-bar-compact" : ""}`}>
      <h2>{ui.summary_heading}</h2>
      <p>{result.summary}</p>
      {!compact && result.summary_bullets.length > 0 ? (
        <ul>
          {result.summary_bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      ) : null}
      <p className="summary-meta">
        {formatTemplate(ui.summary_detected, {
          framework: result.detected_framework,
          project_type: result.detected_project_type,
        })}
      </p>
    </div>
  );
}
