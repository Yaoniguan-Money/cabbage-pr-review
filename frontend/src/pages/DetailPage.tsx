import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  exportUrl,
  fetchDiagramMeta,
  getTask,
  getTaskResult,
  rerunTask,
  type DiagramMetaResponse,
  type TaskRecord,
  type TaskResult,
} from "../api/client";
import AgentProgressBar from "../components/AgentProgressBar";
import DiagramCard from "../components/DiagramCard";
import RerunPanel from "../components/RerunPanel";
import RiskList from "../components/RiskList";
import SummaryBar from "../components/SummaryBar";

type Section = "overview" | "summary" | "diagrams" | "risks" | "missing";

function DiagramMetaLoading() {
  return <div className="meta-loading" aria-busy="true" style={{ minHeight: "4rem" }} />;
}

export default function DetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<TaskRecord | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [diagramMeta, setDiagramMeta] = useState<DiagramMetaResponse | null>(null);
  const [section, setSection] = useState<Section>("overview");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDiagramMeta()
      .then(setDiagramMeta)
      .catch(() => setDiagramMeta(null));
  }, []);

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
        setError(t.error_message || "任务失败");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  }, [taskId]);

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

  if (!taskId) return <p>无效任务</p>;

  const nav: { id: Section; label: string }[] = [
    { id: "overview", label: "总览（默认）" },
    { id: "summary", label: "摘要" },
    { id: "diagrams", label: diagramMeta?.section_label ?? "…" },
    { id: "risks", label: "风险列表" },
    { id: "missing", label: "缺失信息" },
  ];

  const renderDiagramCards = (diagrams: TaskResult["diagrams"], prefix: string) => {
    if (!diagramMeta?.ui_strings) return <DiagramMetaLoading />;
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
    if (!diagramMeta) return <DiagramMetaLoading />;
    if (diagrams.length === 0) return diagramMeta.empty_diagrams;
    return renderDiagramCards(diagrams, prefix);
  };

  return (
    <div>
      <Link to="/" style={{ color: "var(--accent)" }}>
        ← 返回输入
      </Link>
      <p style={{ color: "var(--muted)" }}>任务 ID: {taskId}</p>

      {task && <AgentProgressBar progress={task.agent_progress} />}

      {task && (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          推理模式：{task.llm_mode_label || task.llm_mode || "—"}
          {" · "}
          本次审阅：{task.review_depth_label || task.review_depth_mode || "—"}
          {result?.review_stats
            ? ` | 已扫描 ${result.review_stats.reviewed_atoms}/${result.review_stats.total_atoms} 个差异点`
            : ""}
          {result?.review_stats
            ? ` | Pro ×${result.review_stats.pro_calls} · Flash ×${result.review_stats.flash_calls}`
            : ""}
          {task.compress_stats && task.compress_stats.compress_calls > 0
            ? ` | 本地压缩 ${task.compress_stats.compress_calls} 次（${task.compress_stats.chars_before}→${task.compress_stats.chars_after} 字符）`
            : ""}
          {task.token_stats && task.token_stats.display_segments.length > 0
            ? ` | Token：${task.token_stats.display_segments
                .map((s) => `${s.label} ${s.total_tokens.toLocaleString()}`)
                .join(" · ")}`
            : ""}
        </p>
      )}

      {task?.status === "running" || task?.status === "pending" ? (
        <p>分析进行中，请稍候…</p>
      ) : null}

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="detail-layout">
          <nav>
            <ul className="nav-list">
              {nav.map((n) => (
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
                导出 Markdown
              </button>
            </a>
          </nav>

          <div>
            {result.degradation_notes.length > 0 ? (
              <div className="risk-item medium">
                本次分析包含降级项，请优先查看「缺失信息」确认结果可靠性。
              </div>
            ) : null}

            {result.risks.length === 0 && result.diff_atoms.length > 0 ? (
              <div className="risk-item high">
                当前未提取到风险项，但存在差异原子，可能是审阅结构化输出降级。建议查看「缺失信息」或发起一次重跑。
              </div>
            ) : null}

            {section === "overview" && (
              <div>
                <SummaryBar result={result} />
                <h3 style={{ marginTop: "1.5rem" }}>
                  {diagramMeta?.section_preview_label ?? "…"}
                </h3>
                {renderDiagramCards(
                  result.diagrams.slice(
                    0,
                    diagramMeta?.diagram_count ?? diagramMeta?.diagram_types.length ?? result.diagrams.length,
                  ),
                  "ov",
                )}
                <h3 style={{ marginTop: "1.5rem" }}>风险列表（前 5 条）</h3>
                <RiskList risks={result.risks.slice(0, 5)} />
              </div>
            )}

            {section === "summary" && <SummaryBar result={result} />}

            {section === "diagrams" && (
              <div>{renderDiagramBlock(result.diagrams, "full")}</div>
            )}

            {section === "risks" && <RiskList risks={result.risks} />}

            {section === "missing" && (
              <div>
                <h3>缺失信息 / 受限条件</h3>
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
                {!result.missing_info.length && !result.degradation_notes.length && <p>无</p>}
              </div>
            )}

            <RerunPanel
              atoms={result.diff_atoms}
              disabled={!!task?.rerun_used || task?.status !== "completed"}
              onRerun={handleRerun}
            />
          </div>
        </div>
      )}
    </div>
  );
}
