import type { TaskResult } from "../api/client";
import SummaryBar from "./SummaryBar";

interface AiReviewPanelProps {
  result: TaskResult | null;
  ui: Record<string, string>;
  rulesUi: Record<string, string>;
  runningMessage: string | null;
  isRunning: boolean;
  riskPreview: TaskResult["risks"];
  onViewRisks: () => void;
  onViewDiagrams: () => void;
  showDiagramsAction: boolean;
}

function dominantRiskLevel(risks: TaskResult["risks"]): "high" | "medium" | "low" | "none" {
  if (risks.some((r) => r.risk_level === "high")) return "high";
  if (risks.some((r) => r.risk_level === "medium")) return "medium";
  if (risks.length > 0) return "low";
  return "none";
}

function riskLevelLabel(level: ReturnType<typeof dominantRiskLevel>, ui: Record<string, string>): string {
  switch (level) {
    case "high":
      return ui.risk_level_high;
    case "medium":
      return ui.risk_level_medium;
    case "low":
      return ui.risk_level_low;
    default:
      return ui.risk_level_none;
  }
}

function riskBarWidth(level: ReturnType<typeof dominantRiskLevel>): string {
  switch (level) {
    case "high":
      return "100%";
    case "medium":
      return "66%";
    case "low":
      return "33%";
    default:
      return "8%";
  }
}

export default function AiReviewPanel({
  result,
  ui,
  rulesUi,
  runningMessage,
  isRunning,
  riskPreview,
  onViewRisks,
  onViewDiagrams,
  showDiagramsAction,
}: AiReviewPanelProps) {
  if (isRunning && !result) {
    return (
      <aside className="ai-review-panel">
        <h2 className="ai-panel-title">{ui.ai_panel_title}</h2>
        <p className="sidebar-muted">{runningMessage}</p>
      </aside>
    );
  }
  if (!result) {
    return null;
  }

  const riskLevel = dominantRiskLevel(result.risks);

  return (
    <aside className="ai-review-panel">
      <h2 className="ai-panel-title">{ui.ai_panel_title}</h2>
      <div className="ai-risk-meter">
        <div className="ai-risk-meter-head">
          <span className="ai-risk-label">{ui.overall_risk_label}</span>
          <span className={`ai-risk-value risk-${riskLevel}`}>{riskLevelLabel(riskLevel, ui)}</span>
        </div>
        <div className="ai-risk-bar-track" aria-hidden="true">
          <div
            className={`ai-risk-bar-fill risk-${riskLevel}`}
            style={{ width: riskBarWidth(riskLevel) }}
          />
        </div>
      </div>
      <SummaryBar result={result} ui={ui} compact />
      {riskPreview.length > 0 ? (
        <section className="ai-findings">
          <h3 className="ai-findings-title">{ui.suggested_findings_label}</h3>
          {riskPreview.map((risk) => (
            <article key={risk.id} className={`ai-finding-card risk-item ${risk.risk_level}`}>
              <strong>{risk.title}</strong>
              <p>{risk.description}</p>
            </article>
          ))}
          <button type="button" className="secondary ai-action-btn" onClick={onViewRisks}>
            {ui.view_full_risks}
          </button>
        </section>
      ) : (
        <p className="sidebar-muted">{rulesUi.empty_risks || ui.risk_empty}</p>
      )}
      {showDiagramsAction ? (
        <button type="button" className="secondary ai-action-btn" onClick={onViewDiagrams}>
          {ui.view_diagrams}
        </button>
      ) : null}
    </aside>
  );
}
