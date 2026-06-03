import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import {
  downloadExportMarkdown,
  fetchClientMeta,
  fetchDetailPageMeta,
  fetchDiagramMeta,
  fetchLlmModeOptions,
  fetchRulesCatalog,
  fetchRulesMeta,
  getTask,
  getTaskResult,
  rerunTask,
  type ClientMetaResponse,
  type DetailPageMetaResponse,
  type DiagramMetaResponse,
  type LlmModeOption,
  type RulesCatalogResponse,
  type RulesMetaResponse,
  type TaskRecord,
  type TaskResult,
} from "../api/client";
import { resolveRunningMessage } from "../utils/agentProgressMessage";
import AiReviewPanel from "../components/AiReviewPanel";
import ChangesTable from "../components/ChangesTable";
import CodeDiffPanel from "../components/CodeDiffPanel";
import DemoVerificationPanel from "../components/DemoVerificationPanel";
import DiagramCard from "../components/DiagramCard";
import IndexPanel from "../components/IndexPanel";
import MarkdownReport from "../components/MarkdownReport";
import OverviewPanel from "../components/OverviewPanel";
import ReviewHeader from "../components/ReviewHeader";
import ReviewSidebar from "../components/ReviewSidebar";
import RuleHitsPanel from "../components/RuleHitsPanel";
import RerunPanel from "../components/RerunPanel";
import RiskList from "../components/RiskList";
import SummaryBar from "../components/SummaryBar";
import { SectionTransition } from "../components/motion/SectionTransition";
import ReviewLayout from "../layouts/ReviewLayout";
import { buildPatchFiles } from "../utils/buildPatchFiles";
import { formatTemplate } from "../utils/formatTemplate";
import { loadRuntimeCredentials, isCloudCredentialsEnabled } from "../utils/runtimeCredentialsStorage";

type Section =
  | "overview"
  | "files"
  | "changes"
  | "summary"
  | "report"
  | "rule_hits"
  | "diagrams"
  | "risks"
  | "missing";

function MetaLoading({ label }: { label?: string }) {
  return (
    <div className="meta-loading skeleton-block" aria-busy="true">
      {label ? <p className="sidebar-muted">{label}</p> : null}
    </div>
  );
}

function statusLabel(status: string, ui: Record<string, string>): string {
  switch (status) {
    case "pending":
      return ui.status_pending;
    case "running":
      return ui.status_running;
    case "completed":
      return ui.status_completed;
    case "failed":
      return ui.status_failed;
    default:
      return status;
  }
}

export default function DetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<TaskRecord | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [diagramMeta, setDiagramMeta] = useState<DiagramMetaResponse | null>(null);
  const [rulesMeta, setRulesMeta] = useState<RulesMetaResponse | null>(null);
  const [rulesCatalog, setRulesCatalog] = useState<RulesCatalogResponse | null>(null);
  const [detailMeta, setDetailMeta] = useState<DetailPageMetaResponse | null>(null);
  const [clientMeta, setClientMeta] = useState<ClientMetaResponse | null>(null);
  const [llmOptions, setLlmOptions] = useState<LlmModeOption[]>([]);
  const [section, setSection] = useState<Section>("overview");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [exportLoading, setExportLoading] = useState(false);
  const [metaState, setMetaState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const results = await Promise.allSettled([
        fetchClientMeta(),
        fetchDiagramMeta(),
        fetchRulesMeta(),
        fetchRulesCatalog(),
        fetchDetailPageMeta(),
        fetchLlmModeOptions(),
      ]);
      if (cancelled) return;
      if (results[0].status === "fulfilled") setClientMeta(results[0].value);
      if (results[1].status === "fulfilled") setDiagramMeta(results[1].value);
      if (results[2].status === "fulfilled") setRulesMeta(results[2].value);
      if (results[3].status === "fulfilled") setRulesCatalog(results[3].value);
      if (results[4].status === "fulfilled") setDetailMeta(results[4].value);
      if (results[5].status === "fulfilled") setLlmOptions(results[5].value.options);
      if (results[2].status === "rejected" || results[4].status === "rejected") {
        setMetaState("error");
        return;
      }
      setMetaState("ready");
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const rulesUi = rulesMeta?.ui_strings ?? {};
  const detailUi = detailMeta?.ui_strings ?? {};
  const riskPreviewCount =
    diagramMeta?.overview_risk_preview_count ?? diagramMeta?.diagram_count ?? result?.risks.length ?? 0;

  const activeLlm = useMemo(
    () => llmOptions.find((o) => o.id === task?.llm_mode),
    [llmOptions, task?.llm_mode],
  );

  const isDiagramMode =
    task?.visualization_mode === "diagrams" || activeLlm?.visualization_mode === "diagrams";
  const hasMarkdownReport = Boolean(result?.markdown_report?.trim());
  const showRerun = task?.rerun_supported ?? activeLlm?.rerun_supported ?? true;
  const showTokenStats =
    task?.visualization_mode !== "markdown" &&
    activeLlm?.hide_token_stats !== true &&
    activeLlm?.visualization_mode !== "markdown";
  const showLlmStats =
    isDiagramMode && result?.review_stats && (result.review_stats.pro_calls > 0 || result.review_stats.flash_calls > 0);

  const metaByType = useMemo(() => {
    const map: Record<string, DiagramMetaResponse["diagram_types"][number]> = {};
    for (const item of diagramMeta?.diagram_types || []) {
      map[item.id] = item;
    }
    return map;
  }, [diagramMeta]);

  const patchFiles = useMemo(() => buildPatchFiles(task, result), [task, result]);

  const runningMessage = useMemo(
    () =>
      resolveRunningMessage(
        task?.agent_progress,
        detailMeta?.ui_strings ?? {},
        rulesMeta?.ui_strings?.running_message || "",
      ),
    [task?.agent_progress, detailMeta?.ui_strings, rulesMeta?.ui_strings?.running_message],
  );

  useEffect(() => {
    if (patchFiles.length > 0 && !selectedFile) {
      setSelectedFile(patchFiles[0].filename);
    }
  }, [patchFiles, selectedFile]);

  const poll = useCallback(async () => {
    if (!taskId) return;
    try {
      const t = await getTask(taskId);
      setTask(t);
      if (t.status === "completed") {
        try {
          const r = await getTaskResult(taskId);
          setResult(r);
        } catch {
          if (t.result) {
            setResult(t.result);
          }
        }
      }
      if (t.status === "failed") {
        setError(t.error_message || rulesUi.task_failed_fallback || clientMeta?.error_messages.get_task || "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : rulesUi.load_failed || clientMeta?.error_messages.get_task || "");
    }
  }, [taskId, rulesUi, clientMeta]);

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

  const canExport = Boolean(result ?? task?.result);

  const handleExportMarkdown = useCallback(async () => {
    if (!taskId) return;
    if (!canExport) {
      setError(detailUi.export_no_result || clientMeta?.error_messages.export_markdown || "");
      return;
    }
    const template = detailUi.export_filename_template;
    if (!template) {
      setError(detailUi.export_meta_missing || clientMeta?.error_messages.export_markdown || "");
      return;
    }
    const revokeDelayMs = detailMeta?.export_blob_revoke_delay_ms;
    if (revokeDelayMs == null || revokeDelayMs < 0) {
      setError(detailUi.export_meta_missing || clientMeta?.error_messages.export_markdown || "");
      return;
    }
    try {
      setExportLoading(true);
      setError("");
      await downloadExportMarkdown(
        taskId,
        template,
        revokeDelayMs,
        detailUi.export_empty_blob || clientMeta?.error_messages.export_markdown || "",
      );
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : clientMeta?.error_messages.export_markdown || "",
      );
    } finally {
      setExportLoading(false);
    }
  }, [
    taskId,
    canExport,
    task?.result,
    detailUi.export_filename_template,
    detailUi.export_meta_missing,
    detailUi.export_no_result,
    detailUi.export_empty_blob,
    detailMeta?.export_blob_revoke_delay_ms,
    clientMeta,
  ]);

  if (!taskId) {
    return rulesUi.invalid_task ? <p>{rulesUi.invalid_task}</p> : <MetaLoading label={detailUi.meta_loading} />;
  }

  if (metaState === "loading") {
    return <MetaLoading label={detailUi.meta_loading} />;
  }

  if (metaState === "error" || !rulesMeta || !detailMeta) {
    const loadError =
      detailUi.meta_load_error ||
      clientMeta?.error_messages?.fetch_detail_page_meta ||
      clientMeta?.fatal_ui_error ||
      "页面配置加载失败，请刷新后重试";
    return (
      <div className="meta-loading" role="alert">
        <p>{loadError}</p>
      </div>
    );
  }

  const diagramSectionLabel = diagramMeta?.section_label ?? rulesUi.nav_risks;
  const diagramPreviewLabel = diagramMeta?.section_preview_label ?? diagramSectionLabel;
  const emptyDiagrams = diagramMeta ? diagramMeta.empty_diagrams : "";

  const showRuleHits = Boolean(result?.rule_hits?.length);
  const mergeReportAndRuleHits = hasMarkdownReport && showRuleHits;

  const nav = [
    { id: "overview" as const, label: rulesUi.nav_overview, show: true },
    { id: "files" as const, label: detailUi.nav_files, show: true },
    { id: "changes" as const, label: rulesUi.nav_changes, show: Boolean(result?.diff_atoms.length) },
    { id: "summary" as const, label: rulesUi.nav_summary, show: Boolean(result) },
    { id: "report" as const, label: rulesUi.nav_report, show: hasMarkdownReport },
    {
      id: "rule_hits" as const,
      label: rulesUi.nav_rule_hits,
      show: showRuleHits && !mergeReportAndRuleHits,
    },
    {
      id: "diagrams" as const,
      label: diagramSectionLabel,
      show: isDiagramMode && Boolean(result),
    },
    { id: "risks" as const, label: rulesUi.nav_risks, show: Boolean(result) },
    { id: "missing" as const, label: rulesUi.nav_missing, show: Boolean(result) },
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
    diagramMeta?.diagram_count ?? diagramMeta?.diagram_types.length ?? result?.diagrams.length ?? 0;

  const renderMainContent = () => {
    if (!task) {
      return <MetaLoading label={detailUi.meta_loading} />;
    }

    if (section === "files") {
      return <CodeDiffPanel files={patchFiles} selectedFile={selectedFile} ui={detailUi} />;
    }

    if (!result) {
      if (section === "overview") {
        return (
          <OverviewPanel
            files={patchFiles}
            result={null}
            ui={detailUi}
            rulesUi={rulesUi}
            isMarkdownMode={!isDiagramMode}
            overviewRulesHint={rulesUi.overview_rules_hint || rulesUi.rules_mode_note}
            diagramPreview={null}
            riskPreview={
              <p className="sidebar-muted">
                {runningMessage}
              </p>
            }
          />
        );
      }
      return (
        <p className="sidebar-muted">{runningMessage}</p>
      );
    }

    return (
      <>
        {result.degradation_notes.length > 0 ? (
          <div className="alert-banner alert-banner--warning" role="alert">
            <strong className="alert-banner-title">{detailUi.alert_degradation_title}</strong>
            <p>{rulesUi.degradation_banner}</p>
          </div>
        ) : null}

        {result.risks.length === 0 && result.diff_atoms.length > 0 && isDiagramMode ? (
          <div className="risk-item high">{rulesUi.no_risks_but_atoms_banner}</div>
        ) : null}

        {section === "overview" && (
          <>
            <OverviewPanel
              files={patchFiles}
              result={result}
              ui={detailUi}
              rulesUi={rulesUi}
              isMarkdownMode={!isDiagramMode}
              overviewRulesHint={rulesUi.overview_rules_hint || rulesUi.rules_mode_note}
              diagramPreview={
                isDiagramMode ? (
                  <>
                    <h3 className="content-heading">{diagramPreviewLabel}</h3>
                    {diagramMeta
                      ? renderDiagramCards(result.diagrams.slice(0, previewDiagramCount), "ov")
                      : emptyDiagrams}
                  </>
                ) : null
              }
              riskPreview={<RiskList risks={result.risks.slice(0, riskPreviewCount)} ui={detailUi} />}
            />
            <IndexPanel baseIndex={result.base_index} headIndex={result.head_index} ui={rulesUi} />
            {task.expected_rule_ids?.length ? (
              <DemoVerificationPanel
                expectedRuleIds={task.expected_rule_ids}
                hits={result.rule_hits ?? []}
                catalogRules={rulesCatalog?.rules ?? []}
                ui={rulesUi}
              />
            ) : null}
          </>
        )}

        {section === "changes" && (
          <ChangesTable
            atoms={result.diff_atoms}
            headers={rulesMeta.table_change_headers}
            emptyText={rulesUi.empty_changes}
          />
        )}

        {section === "summary" && <SummaryBar result={result} ui={detailUi} />}

        {section === "report" && result.markdown_report && (
          <>
            <MarkdownReport content={result.markdown_report} />
            {mergeReportAndRuleHits && result.rule_hits ? (
              <>
                <h3 className="content-heading">{rulesUi.section_rule_hits || rulesUi.nav_rule_hits}</h3>
                <RuleHitsPanel
                  hits={result.rule_hits}
                  headers={rulesMeta.table_hit_headers}
                  emptyText={rulesUi.empty_rule_hits}
                  groupByRuleIdDefault={rulesMeta.group_by_rule_id_default ?? true}
                  collapseLowDefault={rulesMeta.collapse_low_default ?? false}
                  groupByRuleIdLabel={rulesUi.group_by_rule_id_label}
                  collapseLowLabel={rulesUi.collapse_low_severity_label}
                  hitCountLabel={rulesUi.hit_count_label}
                  severityFilterAllLabel={detailUi.severity_filter_all}
                />
              </>
            ) : null}
          </>
        )}

        {section === "rule_hits" && result.rule_hits && !mergeReportAndRuleHits && (
          <RuleHitsPanel
            hits={result.rule_hits}
            headers={rulesMeta.table_hit_headers}
            emptyText={rulesUi.empty_rule_hits}
            groupByRuleIdDefault={rulesMeta.group_by_rule_id_default ?? true}
            collapseLowDefault={rulesMeta.collapse_low_default ?? false}
            groupByRuleIdLabel={rulesUi.group_by_rule_id_label}
            collapseLowLabel={rulesUi.collapse_low_severity_label}
            hitCountLabel={rulesUi.hit_count_label}
            severityFilterAllLabel={detailUi.severity_filter_all}
          />
        )}

        {section === "diagrams" && (
          <>
            <h3 className="content-heading">{diagramSectionLabel}</h3>
            <div>{renderDiagramBlock(result.diagrams, "full")}</div>
          </>
        )}

        {section === "risks" && <RiskList risks={result.risks} ui={detailUi} />}

        {section === "missing" && (
          <div>
            <h3>{rulesUi.missing_section_title}</h3>
            {result.missing_info.map((m, i) => (
              <div key={i} className="risk-item low">
                <strong>{m.module}</strong>
                <p>{m.reason}</p>
                {m.suggestion && <p className="risk-suggestion">{m.suggestion}</p>}
              </div>
            ))}
            {result.degradation_notes.map((n, i) => (
              <div key={`d-${i}`} className="risk-item medium">
                {n}
              </div>
            ))}
            {!result.missing_info.length && !result.degradation_notes.length && (
              <p>{rulesUi.empty_missing}</p>
            )}
          </div>
        )}

        {showRerun && result && (
          <RerunPanel
            atoms={result.diff_atoms}
            disabled={!!task.rerun_used || task.status !== "completed"}
            onRerun={handleRerun}
            ui={detailUi}
          />
        )}
      </>
    );
  };

  return (
    <div className="detail-page">
      {clientMeta?.use_mock_llm && clientMeta.mock_mode_banner ? (
        <div className="risk-item medium alert-banner">{clientMeta.mock_mode_banner}</div>
      ) : null}
      {!clientMeta?.use_mock_llm &&
      clientMeta?.cloud_unavailable_banner &&
      !isCloudCredentialsEnabled(loadRuntimeCredentials()) ? (
        <div className="risk-item medium alert-banner" role="status">
          {clientMeta.cloud_unavailable_banner}
        </div>
      ) : null}

      {task && (
        <ReviewHeader
          task={task}
          taskId={taskId}
          ui={detailUi}
          statusLabel={statusLabel(task.status, detailUi)}
          metaExtra={
            <>
              {result?.review_stats && isDiagramMode ? (
                <span className="meta-chip">
                  {formatTemplate(detailUi.meta_atoms_scanned, {
                    reviewed: result.review_stats.reviewed_atoms,
                    total: result.review_stats.total_atoms,
                  })}
                </span>
              ) : null}
              {showLlmStats && result?.review_stats ? (
                <span className="meta-chip">
                  {formatTemplate(detailUi.meta_llm_calls, {
                    pro: result.review_stats.pro_calls,
                    flash: result.review_stats.flash_calls,
                  })}
                </span>
              ) : null}
              {task.compress_stats && task.compress_stats.compress_calls > 0 ? (
                <span className="meta-chip">
                  {formatTemplate(detailUi.meta_compress, {
                    calls: task.compress_stats.compress_calls,
                    before: task.compress_stats.chars_before,
                    after: task.compress_stats.chars_after,
                  })}
                </span>
              ) : null}
              {showTokenStats && task.token_stats && task.token_stats.display_segments.length > 0 ? (
                <span className="meta-chip">
                  {detailUi.meta_token_segment?.includes("{label}")
                    ? task.token_stats.display_segments
                        .map((s) =>
                          formatTemplate(detailUi.meta_token_segment, {
                            label: s.label,
                            total: s.total_tokens.toLocaleString(),
                          }),
                        )
                        .join(" · ")
                    : task.token_stats.display_segments
                        .map((s) => `${s.label}: ${s.total_tokens.toLocaleString()}`)
                        .join(" · ")}
                </span>
              ) : null}
            </>
          }
        />
      )}

      {task?.status === "running" || task?.status === "pending" ? (
        <p className="running-banner">{runningMessage}</p>
      ) : null}

      {error && <div className="error">{error}</div>}

      {task ? (
        <ReviewLayout
          sidebar={
            <ReviewSidebar
              taskId={taskId}
              nav={nav}
              section={section}
              onSectionChange={(id) => setSection(id as Section)}
              files={patchFiles}
              selectedFile={selectedFile}
              onSelectFile={setSelectedFile}
              ui={detailUi}
              rulesUi={rulesUi}
              filesSidebarLabel={detailUi.files_sidebar_label}
              exportLabel={rulesUi.export_markdown}
              exportLoading={exportLoading}
              exportLoadingLabel={detailUi.export_loading}
              exportDisabled={!canExport || exportLoading}
              exportDisabledHint={detailUi.export_disabled_hint}
              onExport={handleExportMarkdown}
              onJumpDiagrams={() => setSection("diagrams")}
              showDiagramsLink={isDiagramMode && Boolean(result)}
              diagramsLinkLabel={detailUi.view_diagrams}
            />
          }
          main={<SectionTransition sectionKey={section}>{renderMainContent()}</SectionTransition>}
          aside={
            <AiReviewPanel
              result={result}
              ui={detailUi}
              rulesUi={rulesUi}
              runningMessage={runningMessage}
              isRunning={task.status === "running" || task.status === "pending"}
              riskPreview={result?.risks.slice(0, riskPreviewCount) ?? []}
              onViewRisks={() => setSection("risks")}
              onViewDiagrams={() => setSection("diagrams")}
              showDiagramsAction={isDiagramMode && Boolean(result?.diagrams.length)}
            />
          }
        />
      ) : (
        <MetaLoading label={detailUi.meta_loading} />
      )}
    </div>
  );
}
