import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  exportUrl,
  getTask,
  getTaskResult,
  rerunTask,
  type TaskRecord,
  type TaskResult,
} from "../api/client";
import AgentProgressBar from "../components/AgentProgressBar";
import MermaidDiagram from "../components/MermaidDiagram";
import RerunPanel from "../components/RerunPanel";
import RiskList from "../components/RiskList";
import SummaryBar from "../components/SummaryBar";

const DIAGRAM_TITLES: Record<string, string> = {
  architecture: "原项目架构 / 流程图",
  impact_overlay: "PR 影响叠加图",
  path_compare: "关键路径前后对比图",
};

type Section = "overview" | "summary" | "diagrams" | "risks" | "missing";

export default function DetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<TaskRecord | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [section, setSection] = useState<Section>("overview");
  const [error, setError] = useState("");

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
    { id: "diagrams", label: "三张图" },
    { id: "risks", label: "风险列表" },
    { id: "missing", label: "缺失信息" },
  ];

  return (
    <div>
      <Link to="/" style={{ color: "var(--accent)" }}>
        ← 返回输入
      </Link>
      <p style={{ color: "var(--muted)" }}>任务 ID: {taskId}</p>

      {task && <AgentProgressBar progress={task.agent_progress} />}

      {task && (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          本次审阅：{task.review_depth_label || task.review_depth_mode || "标准审阅"}
          {result?.review_stats
            ? ` | 已扫描 ${result.review_stats.reviewed_atoms}/${result.review_stats.total_atoms} 个差异点`
            : ""}
          {result?.review_stats
            ? ` | Pro ×${result.review_stats.pro_calls} · Flash ×${result.review_stats.flash_calls}`
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
                <h3 style={{ marginTop: "1.5rem" }}>三张图（预览）</h3>
                {result.diagrams.slice(0, 3).map((d, i) => (
                  <div key={i}>
                    <h4>{DIAGRAM_TITLES[d.diagram_type] || d.diagram_type}</h4>
                    <MermaidDiagram code={d.mermaid} id={`${taskId}-ov-${i}`} />
                  </div>
                ))}
                <h3 style={{ marginTop: "1.5rem" }}>风险列表（前 5 条）</h3>
                <RiskList risks={result.risks.slice(0, 5)} />
              </div>
            )}

            {section === "summary" && <SummaryBar result={result} />}

            {section === "diagrams" && (
              <div>
                {result.diagrams.map((d, i) => (
                  <div key={i}>
                    <h3>{DIAGRAM_TITLES[d.diagram_type] || d.diagram_type}</h3>
                    <MermaidDiagram code={d.mermaid} id={`${taskId}-${i}`} />
                  </div>
                ))}
                {result.diagrams.length === 0 && <p>暂无图表</p>}
              </div>
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
