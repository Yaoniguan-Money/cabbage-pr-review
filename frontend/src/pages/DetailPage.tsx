import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  exportUrl,
  fetchClientMeta,
  fetchDiagramMeta,
  fetchLlmModeOptions,
  fetchRulesMeta,
  getTask,
  getTaskResult,
  rerunTask,
  type ClientMetaResponse,
  type DiagramMetaResponse,
  type LlmModeOption,
  type RulesMetaResponse,
  type TaskRecord,
  type TaskResult,
} from "../api/client";
import AgentProgressBar from "../components/AgentProgressBar";
import DiagramCard from "../components/DiagramCard";
import MarkdownReport from "../components/MarkdownReport";
import RuleHitsPanel from "../components/RuleHitsPanel";
import RerunPanel from "../components/RerunPanel";
import RiskList from "../components/RiskList";
import SummaryBar from "../components/SummaryBar";

type Section = "overview" | "summary" | "report" | "rule_hits" | "diagrams" | "risks" | "missing";

function MetaLoading() {
  return <div className="meta-loading" aria-busy="true" style={{ minHeight: "4rem" }} />;
}

export default function DetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<TaskRecord | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [diagramMeta, setDiagramMeta] = useState<DiagramMetaResponse | null>(null);
  const [rulesMeta, setRulesMeta] = useState<RulesMetaResponse | null>(null);
  const [clientMeta, setClientMeta] = useState<ClientMetaResponse | null>(null);
  const [llmOptions, setLlmOptions] = useState<LlmModeOption[]>([]);
  const [section, setSection] = useState<Section>("overview");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchClientMeta().then(setClientMeta).catch(() => setClientMeta(null));
    fetchDiagramMeta().then(setDiagramMeta).catch(() => setDiagramMeta(null));
    fetchRulesMeta().then(setRulesMeta).catch(() => setRulesMeta(null));
    fetchLlmModeOptions()
      .then((data) => setLlmOptions(data.options))
      .catch(() => setLlmOptions([]));
  }, []);

  const ui = rulesMeta?.ui_strings;
  const riskPreviewCount =
    diagramMeta?.overview_risk_preview_count ?? diagramMeta?.diagram_count ?? result?.risks.length ?? 0;

  const activeLlm = useMemo(
    () => llmOptions.find((o) => o.id === task?.llm_mode),
    [llmOptions, task?.llm_mode],
  );

  const isMarkdownMode =
    task?.visualization_mode === "markdown" ||
    activeLlm?.visualization_mode === "markdown" ||
    Boolean(result?.markdown_report?.trim());
  const showRerun = task?.rerun_supported ?? activeLlm?.rerun_supported ?? true;
  const showTokenStats =
    task?.visualization_mode !== "markdown" &&
    activeLlm?.hide_token_stats !== true &&
    activeLlm?.visualization_mode !== "markdown";
  const showLlmStats =
    !isMarkdownMode && result?.review_stats && (result.review_stats.pro_calls > 0 || result.review_stats.flash_calls > 0);

  const metaByType = useMemo(() => {
    const map: Record<string, DiagramMetaResponse["diagram_types"][number]> = {};
    for (const item of diagramMeta?.diagram_types || []) {
      map[item.id] = item;
    }
    return map;
  }, [diagramMeta]);

  const poll = useCallback(async () => {
    if (!taskId) return;
    try {
      const t = await getTask(taskId);
      setTask(t);
      if (t.status === "completed") {
        const r = await getTaskResult(taskId);
        setResult(r);
      }
      if (t.status === "failed") {
        setError(t.error_message || ui?.task_failed_fallback || clientMeta?.error_messages.get_task || "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : ui?.load_failed || clientMeta?.error_messages.get_task || "");
    }
  }, [taskId, ui, clientMeta]);

  useEffect(() => {
    poll();
    const timer = setInterval(() => {
      if (task?.status === "completed" || task?.status === "failed") return;
      poll();
    }, 2000);
    return () => clearInterval(timer);
  }, [poll, task?.status]);

  const handleRerun = async (paths: string[], atomIds: string[]) => {
    if (!taskId) return;
    await rerunTask(taskId, { extra_context_paths: paths, focus_atom_ids: atomIds });
    setResult(null);
    setTask(null);
    poll();
  };

  if (!taskId) {
    return ui ? <p>{ui.invalid_task}</p> : <MetaLoading />;
  }

  if (!ui) {
    return <MetaLoading />;
  }

  const diagramSectionLabel = diagramMeta?.section_label ?? ui.nav_risks;
  const diagramPreviewLabel = diagramMeta?.section_preview_label ?? diagramSectionLabel;
  const emptyDiagrams = diagramMeta ? diagramMeta.empty_diagrams : "";

  const showRuleHits = Boolean(result?.rule_hits?.length);
  const mergeReportAndRuleHits =
    isMarkdownMode && showRuleHits && Boolean(result?.markdown_report?.trim());

  const nav: { id: Section; label: string; show: boolean }[] = [
    { id: "overview", label: ui.nav_overview, show: true },
    { id: "summary", label: ui.nav_summary, show: true },
    { id: "report", label: ui.nav_report, show: isMarkdownMode && Boolean(result?.markdown_report?.trim()) },
    {
      id: "rule_hits",
      label: ui.nav_rule_hits || "规则命中",
      show: showRuleHits && !mergeReportAndRuleHits,
    },
    { id: "diagrams", label: diagramSectionLabel, show: !isMarkdownMode && Boolean(diagramMeta) },
    { id: "risks", label: ui.nav_risks, show: true },
    { id: "missing", label: ui.nav_missing, show: true },
  ];

  const renderDiagramCards = (diagrams: TaskResult["diagrams"], prefix: string) => {
    if (!diagramMeta) return null;
    return diagrams.map((d, i) => (
      <DiagramCard
        key={`${d.diagram_type}-${i}`}
        diagram={d}
        metaByType={metaByType}
        defaultLegend={diagramMeta.default_legend}
        uiStrings={diagramMeta.ui_strings}
        renderId={`${taskId}-${prefix}-${i}`}
      />
    ));
  };

  const renderDiagramBlock = (diagrams: TaskResult["diagrams"], prefix: string) => {
    if (diagrams.length === 0) return emptyDiagrams;
    if (!diagramMeta) return emptyDiagrams;
    return renderDiagramCards(diagrams, prefix);
  };

  const previewDiagramCount =
    diagramMeta?.diagram_count ??
    diagramMeta?.diagram_types.length ??
    result?.diagrams.length ??
    0;

  return (
    <div>
      <Link to="/" style={{ color: "var(--accent)" }}>
        {ui.back_link}
      </Link>
      {clientMeta?.use_mock_llm && clientMeta.mock_mode_banner ? (
        <div className="risk-item medium" style={{ marginTop: "0.75rem" }}>
          {clientMeta.mock_mode_banner}
        </div>
      ) : null}
      <p style={{ color: "var(--muted)" }}>任务 ID: {taskId}</p>

      {task && <AgentProgressBar progress={task.agent_progress} />}

      {task && (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          推理模式：{task.llm_mode_label || task.llm_mode || "—"}
          {" · "}
          本次审阅：{task.review_depth_label || task.review_depth_mode || "—"}
          {result?.review_stats && !isMarkdownMode
            ? ` | 已扫描 ${result.review_stats.reviewed_atoms}/${result.review_stats.total_atoms} 个差异点`
            : ""}
          {showLlmStats && result?.review_stats
            ? ` | Pro ×${result.review_stats.pro_calls} · Flash ×${result.review_stats.flash_calls}`
            : ""}
          {task.compress_stats && task.compress_stats.compress_calls > 0
            ? ` | 本地压缩 ${task.compress_stats.compress_calls} 次（${task.compress_stats.chars_before}→${task.compress_stats.chars_after} 字符）`
            : ""}
          {showTokenStats && task.token_stats && task.token_stats.display_segments.length > 0
            ? ` | Token：${task.token_stats.display_segments
                .map((s) => `${s.label} ${s.total_tokens.toLocaleString()}`)
                .join(" · ")}`
            : ""}
        </p>
      )}

      {task?.status === "running" || task?.status === "pending" ? <p>{ui.running_message}</p> : null}

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="detail-layout">
          <nav aria-label="任务详情导航">
            <ul className="nav-list">
              {nav
                .filter((n) => n.show)
                .map((n) => (
                  <li key={n.id}>
                    <button
                      type="button"
                      className={section === n.id ? "active" : ""}
                      onClick={() => setSection(n.id)}
                    >
                      {n.label}
                    </button>
                  </li>
                ))}
            </ul>
            <a href={exportUrl(taskId)} target="_blank" rel="noreferrer">
              <button type="button" className="secondary" style={{ width: "100%" }}>
                {ui.export_markdown}
              </button>
            </a>
          </nav>

          <div>
            {result.degradation_notes.length > 0 ? (
              <div className="risk-item medium">{ui.degradation_banner}</div>
            ) : null}

            {result.risks.length === 0 && result.diff_atoms.length > 0 && !isMarkdownMode ? (
              <div className="risk-item high">{ui.no_risks_but_atoms_banner}</div>
            ) : null}

            {section === "overview" && (
              <div>
                <SummaryBar result={result} />
                {isMarkdownMode ? (
                  <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
                    {ui.overview_rules_hint || ui.rules_mode_note}
                  </p>
                ) : (
                  <>
                    <h3 style={{ marginTop: "1.5rem" }}>{diagramPreviewLabel}</h3>
                    {diagramMeta
                      ? renderDiagramCards(result.diagrams.slice(0, previewDiagramCount), "ov")
                      : emptyDiagrams}
                  </>
                )}
                <h3 style={{ marginTop: "1.5rem" }}>{ui.overview_risks_preview_title}</h3>
                <RiskList risks={result.risks.slice(0, riskPreviewCount)} />
              </div>
            )}

            {section === "summary" && <SummaryBar result={result} />}

            {section === "report" && result.markdown_report && (
              <>
                <MarkdownReport content={result.markdown_report} />
                {mergeReportAndRuleHits && result.rule_hits ? (
                  <>
                    <h3 style={{ marginTop: "1.5rem" }}>{ui.section_rule_hits || ui.nav_rule_hits}</h3>
                    <RuleHitsPanel
                      hits={result.rule_hits}
                      headers={rulesMeta ? rulesMeta.table_hit_headers : []}
                      emptyText={ui.empty_rule_hits}
                      groupByRuleIdDefault={rulesMeta?.group_by_rule_id_default ?? true}
                      collapseLowDefault={rulesMeta?.collapse_low_default ?? false}
                      groupByRuleIdLabel={ui.group_by_rule_id_label}
                      collapseLowLabel={ui.collapse_low_severity_label}
                      hitCountLabel={ui.hit_count_label}
                    />
                  </>
                ) : null}
              </>
            )}

            {section === "rule_hits" && result.rule_hits && !mergeReportAndRuleHits && (
              <RuleHitsPanel
                hits={result.rule_hits}
                headers={rulesMeta ? rulesMeta.table_hit_headers : []}
                emptyText={ui.empty_rule_hits}
                groupByRuleIdDefault={rulesMeta?.group_by_rule_id_default ?? true}
                collapseLowDefault={rulesMeta?.collapse_low_default ?? false}
                groupByRuleIdLabel={ui.group_by_rule_id_label}
                collapseLowLabel={ui.collapse_low_severity_label}
                hitCountLabel={ui.hit_count_label}
              />
            )}

            {section === "diagrams" && <div>{renderDiagramBlock(result.diagrams, "full")}</div>}

            {section === "risks" && <RiskList risks={result.risks} />}

            {section === "missing" && (
              <div>
                <h3>{ui.missing_section_title}</h3>
                {result.missing_info.map((m, i) => (
                  <div key={i} className="risk-item low">
                    <strong>{m.module}</strong>
                    <p>{m.reason}</p>
                    {m.suggestion && <p style={{ fontSize: "0.9rem" }}>{m.suggestion}</p>}
                  </div>
                ))}
                {result.degradation_notes.map((n, i) => (
                  <div key={`d-${i}`} className="risk-item medium">
                    {n}
                  </div>
                ))}
                {!result.missing_info.length && !result.degradation_notes.length && (
                  <p>{ui.empty_missing}</p>
                )}
              </div>
            )}

            {showRerun && (
              <RerunPanel
                atoms={result.diff_atoms}
                disabled={!!task?.rerun_used || task?.status !== "completed"}
                onRerun={handleRerun}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
