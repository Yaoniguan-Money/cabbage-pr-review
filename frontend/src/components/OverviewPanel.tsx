import type { ReactNode } from "react";
import type { PrPatchFile, TaskResult } from "../api/client";
import { RevealStagger, RevealStaggerItem } from "./motion/Reveal";
import { formatTemplate } from "../utils/formatTemplate";

interface OverviewPanelProps {
  files: PrPatchFile[];
  result: TaskResult | null;
  ui: Record<string, string>;
  rulesUi: Record<string, string>;
  isMarkdownMode: boolean;
  overviewRulesHint: string;
  diagramPreview: ReactNode;
  riskPreview: ReactNode;
}

export default function OverviewPanel({
  files,
  result,
  ui,
  rulesUi,
  isMarkdownMode,
  overviewRulesHint,
  diagramPreview,
  riskPreview,
}: OverviewPanelProps) {
  const additions = files.reduce((sum, f) => sum + (f.additions ?? 0), 0);
  const deletions = files.reduce((sum, f) => sum + (f.deletions ?? 0), 0);
  const reviewed = result?.review_stats?.reviewed_atoms;
  const total = result?.review_stats?.total_atoms;

  return (
    <div className="overview-panel">
      <h3 className="content-heading">{ui.stat_checks}</h3>
      <RevealStagger className="stat-cards">
        <RevealStaggerItem className="stat-card">
          <span className="stat-label">{ui.stat_files}</span>
          <strong className="stat-value">{files.length}</strong>
        </RevealStaggerItem>
        <RevealStaggerItem className="stat-card">
          <span className="stat-label">{ui.stat_additions}</span>
          <strong className="stat-value stat-add">+{additions}</strong>
        </RevealStaggerItem>
        <RevealStaggerItem className="stat-card">
          <span className="stat-label">{ui.stat_deletions}</span>
          <strong className="stat-value stat-del">-{deletions}</strong>
        </RevealStaggerItem>
        {reviewed != null && total != null ? (
          <RevealStaggerItem className="stat-card">
            <span className="stat-label">{ui.stat_review_progress}</span>
            <strong className="stat-value">
              {formatTemplate(ui.meta_atoms_scanned, { reviewed, total })}
            </strong>
          </RevealStaggerItem>
        ) : null}
      </RevealStagger>

      {isMarkdownMode ? <p className="section-hint">{overviewRulesHint}</p> : diagramPreview}

      <section className="overview-risks">
        <h3 className="content-heading">{rulesUi.overview_risks_preview_title}</h3>
        {riskPreview}
      </section>
    </div>
  );
}
