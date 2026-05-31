import { useMemo, useState } from "react";
import type { RiskItem } from "../api/client";
import { formatTemplate } from "../utils/formatTemplate";

const RISK_ORDER = { high: 0, medium: 1, low: 2 };
const CONF_ORDER = { high: 0, medium: 1, low: 2 };

export default function RiskList({
  risks,
  ui,
}: {
  risks: RiskItem[];
  ui: Record<string, string>;
}) {
  const [sortBy, setSortBy] = useState<"risk" | "confidence">("risk");

  const sorted = useMemo(() => {
    const copy = [...risks];
    if (sortBy === "risk") {
      copy.sort((a, b) => RISK_ORDER[a.risk_level] - RISK_ORDER[b.risk_level]);
    } else {
      copy.sort((a, b) => CONF_ORDER[a.confidence] - CONF_ORDER[b.confidence]);
    }
    return copy;
  }, [risks, sortBy]);

  return (
    <div>
      <div className="risk-toolbar">
        <label>{ui.risk_sort_label}</label>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "risk" | "confidence")}>
          <option value="risk">{ui.risk_sort_by_risk}</option>
          <option value="confidence">{ui.risk_sort_by_confidence}</option>
        </select>
      </div>
      {sorted.map((r) => (
        <div key={r.id} className={`risk-item ${r.risk_level}`}>
          <strong>{r.title}</strong>
          <div className="risk-meta">
            {formatTemplate(ui.risk_meta, { level: r.risk_level, confidence: r.confidence })}
          </div>
          <p>{r.description}</p>
          {r.evidence && (
            <p className="risk-evidence">
              {formatTemplate(ui.risk_evidence, {
                text: `${r.evidence.slice(0, 300)}${r.evidence.length > 300 ? "…" : ""}`,
              })}
            </p>
          )}
          {r.suggestion && (
            <p className="risk-suggestion">{formatTemplate(ui.risk_suggestion, { text: r.suggestion })}</p>
          )}
        </div>
      ))}
      {sorted.length === 0 && <p>{ui.risk_empty}</p>}
    </div>
  );
}
