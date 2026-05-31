import { useMemo, useState } from "react";

import type { RuleHitRecord } from "../api/client";

interface RuleHitsPanelProps {
  hits: RuleHitRecord[];
  headers: string[];
  emptyText: string;
  groupByRuleIdDefault?: boolean;
  collapseLowDefault?: boolean;
  groupByRuleIdLabel?: string;
  collapseLowLabel?: string;
  hitCountLabel?: string;
  severityFilterAllLabel?: string;
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

function rowCells(hit: RuleHitRecord): string[] {
  return [
    hit.rule_id,
    hit.severity,
    hit.file_path,
    hit.evidence.slice(0, 200),
    hit.message,
  ];
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
  severityFilterAllLabel = "全部",
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
  const columnCount = headers.length;

  if (!hits.length) {
    return <p>{emptyText}</p>;
  }

  const renderRow = (hit: RuleHitRecord, index: number) => (
    <tr key={`${hit.rule_id}-${hit.file_path}-${index}`}>
      {rowCells(hit).slice(0, columnCount).map((cell, cellIndex) => (
        <td key={cellIndex}>{cell}</td>
      ))}
    </tr>
  );

  const renderGroup = (group: RuleHitGroup) => (
    <tbody key={group.rule_id}>
      <tr className="rule-hits-group-header">
        <td colSpan={columnCount}>
          {group.rule_id} · {group.severity.toUpperCase()} · {formatHitCount(hitCountLabel, group.hits.length)}
        </td>
      </tr>
      {group.hits.map((hit, index) => renderRow(hit, index))}
    </tbody>
  );

  return (
    <div>
      <div className="rule-hits-toolbar">
        {severities.map((item) => (
          <button
            key={item}
            type="button"
            className={`btn-chip secondary ${severity === item ? "active" : ""}`}
            onClick={() => setSeverity(item)}
          >
            {item === "all" ? severityFilterAllLabel : item}
          </button>
        ))}
        <label>
          <input type="checkbox" checked={groupByRule} onChange={(e) => setGroupByRule(e.target.checked)} />
          {groupByRuleIdLabel}
        </label>
        <label>
          <input type="checkbox" checked={collapseLow} onChange={(e) => setCollapseLow(e.target.checked)} />
          {collapseLowLabel}
        </label>
      </div>
      <table className="rule-hits-table">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
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
