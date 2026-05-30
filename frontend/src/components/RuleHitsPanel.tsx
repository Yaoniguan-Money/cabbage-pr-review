import { useMemo, useState } from "react";

export interface RuleHitRecord {
  rule_id: string;
  severity: string;
  file_path: string;
  evidence: string;
  message: string;
}

interface RuleHitsPanelProps {
  hits: RuleHitRecord[];
  headers: string[];
  emptyText: string;
  groupByRuleIdDefault?: boolean;
  collapseLowDefault?: boolean;
  groupByRuleIdLabel?: string;
  collapseLowLabel?: string;
  hitCountLabel?: string;
}

interface RuleHitGroup {
  rule_id: string;
  severity: string;
  hits: RuleHitRecord[];
}

function groupHits(hits: RuleHitRecord[]): RuleHitGroup[] {
  const map = new Map<string, RuleHitGroup>();
  for (const hit of hits) {
    const existing = map.get(hit.rule_id);
    if (existing) {
      existing.hits.push(hit);
    } else {
      map.set(hit.rule_id, {
        rule_id: hit.rule_id,
        severity: hit.severity,
        hits: [hit],
      });
    }
  }
  return Array.from(map.values());
}

function formatHitCount(template: string, count: number): string {
  return template.replace("{count}", String(count));
}

export default function RuleHitsPanel({
  hits,
  headers,
  emptyText,
  groupByRuleIdDefault = true,
  collapseLowDefault = false,
  groupByRuleIdLabel = "按规则分组",
  collapseLowLabel = "折叠 LOW",
  hitCountLabel = "命中 {count} 次",
}: RuleHitsPanelProps) {
  const [severity, setSeverity] = useState<string>("all");
  const [groupByRule, setGroupByRule] = useState(groupByRuleIdDefault);
  const [collapseLow, setCollapseLow] = useState(collapseLowDefault);

  const severities = useMemo(() => {
    const set = new Set(hits.map((h) => h.severity.toUpperCase()));
    return ["all", ...Array.from(set).sort()];
  }, [hits]);

  const filtered = useMemo(() => {
    let list = hits;
    if (severity !== "all") {
      list = list.filter((h) => h.severity.toUpperCase() === severity);
    }
    if (collapseLow) {
      list = list.filter((h) => h.severity.toUpperCase() !== "LOW");
    }
    return list;
  }, [hits, severity, collapseLow]);

  const groups = useMemo(() => groupHits(filtered), [filtered]);

  if (!hits.length) {
    return <p>{emptyText}</p>;
  }

  const renderRow = (hit: RuleHitRecord, index: number) => (
    <tr key={`${hit.rule_id}-${hit.file_path}-${index}`}>
      <td style={{ padding: "0.5rem", verticalAlign: "top" }}>{hit.rule_id}</td>
      <td style={{ padding: "0.5rem", verticalAlign: "top" }}>{hit.severity}</td>
      <td style={{ padding: "0.5rem", verticalAlign: "top" }}>{hit.file_path}</td>
      <td style={{ padding: "0.5rem", verticalAlign: "top", wordBreak: "break-word" }}>
        {hit.evidence.slice(0, 200)}
      </td>
    </tr>
  );

  const renderGroup = (group: RuleHitGroup) => (
    <tbody key={group.rule_id}>
      <tr>
        <td colSpan={headers.length} style={{ padding: "0.5rem", fontWeight: 600, borderBottom: "1px solid var(--border)" }}>
          {group.rule_id} · {group.severity.toUpperCase()} · {formatHitCount(hitCountLabel, group.hits.length)}
        </td>
      </tr>
      {group.hits.map((hit, index) => renderRow(hit, index))}
    </tbody>
  );

  return (
    <div>
      <div style={{ marginBottom: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
        {severities.map((item) => (
          <button
            key={item}
            type="button"
            className={severity === item ? "active" : "secondary"}
            onClick={() => setSeverity(item)}
          >
            {item === "all" ? "全部" : item}
          </button>
        ))}
        <label style={{ display: "flex", alignItems: "center", gap: "0.35rem", marginLeft: "0.5rem" }}>
          <input type="checkbox" checked={groupByRule} onChange={(e) => setGroupByRule(e.target.checked)} />
          {groupByRuleIdLabel}
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <input type="checkbox" checked={collapseLow} onChange={(e) => setCollapseLow(e.target.checked)} />
          {collapseLowLabel}
        </label>
      </div>
      <table className="rule-hits-table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header} style={{ textAlign: "left", padding: "0.5rem", borderBottom: "1px solid var(--border)" }}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        {groupByRule
          ? groups.map((group) => renderGroup(group))
          : (
            <tbody>{filtered.map((hit, index) => renderRow(hit, index))}</tbody>
          )}
      </table>
    </div>
  );
}
