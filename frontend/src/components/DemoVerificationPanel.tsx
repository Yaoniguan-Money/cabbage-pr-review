import { useMemo } from "react";

import type { RuleHitRecord, RulesCatalogEntry } from "../api/client";

interface DemoVerificationPanelProps {
  expectedRuleIds: string[];
  hits: RuleHitRecord[];
  catalogRules: RulesCatalogEntry[];
  ui: Record<string, string>;
}

export default function DemoVerificationPanel({
  expectedRuleIds,
  hits,
  catalogRules,
  ui,
}: DemoVerificationPanelProps) {
  const actualIds = useMemo(() => new Set(hits.map((h) => h.rule_id)), [hits]);
  const expectedSet = useMemo(() => new Set(expectedRuleIds), [expectedRuleIds]);

  const hitIds = expectedRuleIds.filter((id) => actualIds.has(id));
  const missIds = expectedRuleIds.filter((id) => !actualIds.has(id));
  const extraIds = [...actualIds].filter((id) => !expectedSet.has(id));

  const matcherById = useMemo(() => {
    const map = new Map<string, string>();
    for (const rule of catalogRules) {
      map.set(rule.id, rule.matcher_type || "regex");
    }
    return map;
  }, [catalogRules]);

  if (!expectedRuleIds.length) {
    return null;
  }

  const renderGroup = (title: string, ids: string[], className: string) => {
    if (!ids.length) return null;
    return (
      <div className={`demo-verify-group ${className}`}>
        <h4 className="demo-verify-group-title">{title}</h4>
        <ul className="demo-verify-list">
          {ids.map((id) => (
            <li key={id}>
              <code>{id}</code>
              {matcherById.has(id) ? (
                <span className="demo-verify-matcher">
                  {ui.demo_verification_matcher}: {matcherById.get(id)}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <section className="demo-verification card" aria-label={ui.demo_verification_title}>
      <h3 className="content-heading">{ui.demo_verification_title}</h3>
      {renderGroup(ui.demo_verification_hit, hitIds, "demo-verify-hit")}
      {renderGroup(ui.demo_verification_miss, missIds, "demo-verify-miss")}
      {renderGroup(ui.demo_verification_extra, extraIds, "demo-verify-extra")}
    </section>
  );
}
