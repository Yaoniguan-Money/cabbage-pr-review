import { useMemo, useState } from "react";
import type { RiskItem } from "../api/client";

const RISK_ORDER = { high: 0, medium: 1, low: 2 };
const CONF_ORDER = { high: 0, medium: 1, low: 2 };

export default function RiskList({ risks }: { risks: RiskItem[] }) {
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
      <div style={{ marginBottom: "0.75rem" }}>
        <label>排序：</label>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "risk" | "confidence")}>
          <option value="risk">按风险等级</option>
          <option value="confidence">按置信度</option>
        </select>
      </div>
      {sorted.map((r) => (
        <div key={r.id} className={`risk-item ${r.risk_level}`}>
          <strong>{r.title}</strong>
          <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            风险: {r.risk_level} | 置信度: {r.confidence}
          </div>
          <p>{r.description}</p>
        </div>
      ))}
      {sorted.length === 0 && <p>暂无风险项</p>}
    </div>
  );
}
