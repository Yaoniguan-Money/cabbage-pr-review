import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createTask,
  fetchExamples,
  type ExamplePR,
  type InputType,
} from "../api/client";

type Tab = InputType;

const PROJECT_TYPES = ["python-api", "node-api", "frontend", "python", "typescript", "unknown"];
const FRAMEWORKS = ["FastAPI", "Express", "React/Vite", "Python", "TypeScript/JavaScript", "unknown"];

export default function InputPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("pr_url");
  const [value, setValue] = useState("");
  const [projectType, setProjectType] = useState("unknown");
  const [framework, setFramework] = useState("unknown");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [examples, setExamples] = useState<ExamplePR[]>([]);

  useEffect(() => {
    fetchExamples().then(setExamples).catch(() => {});
  }, []);

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      const task = await createTask({
        input_type: tab,
        value,
        project_type: projectType !== "unknown" ? projectType : undefined,
        framework: framework !== "unknown" ? framework : undefined,
      });
      navigate(`/tasks/${task.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败");
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: Tab; title: string; hint: string }[] = [
    { id: "pr_url", title: "PR URL", hint: "https://github.com/owner/repo/pull/123" },
    { id: "patch", title: "Patch / Diff", hint: "粘贴 diff 或 patch 文本" },
    { id: "local_path", title: "本地仓库路径", hint: "例如 C:\\projects\\my-app" },
  ];

  return (
    <div>
      <div className="card-grid">
        {tabs.map((t) => (
          <div
            key={t.id}
            className={`card ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
            role="button"
          >
            <h3>{t.title}</h3>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{t.hint}</p>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginTop: "1rem" }}>
        <label>输入内容</label>
        {tab === "patch" ? (
          <textarea value={value} onChange={(e) => setValue(e.target.value)} rows={8} placeholder="diff --git ..." />
        ) : (
          <input value={value} onChange={(e) => setValue(e.target.value)} placeholder={tabs.find((x) => x.id === tab)?.hint} />
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
          <div>
            <label>项目类型（可手动确认）</label>
            <select value={projectType} onChange={(e) => setProjectType(e.target.value)}>
              {PROJECT_TYPES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>框架（可手动切换）</label>
            <select value={framework} onChange={(e) => setFramework(e.target.value)}>
              {FRAMEWORKS.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
        <button onClick={submit} disabled={loading || !value.trim()}>
          {loading ? "创建任务中…" : "开始分析"}
        </button>
      </div>

      <div className="examples card">
        <h3>官方示例 PR（一键填充）</h3>
        {examples.map((ex) => (
          <button
            key={ex.id}
            className="secondary example-chip"
            type="button"
            onClick={() => {
              setTab("pr_url");
              setValue(ex.pr_url);
            }}
          >
            {ex.title}
          </button>
        ))}
      </div>
    </div>
  );
}
