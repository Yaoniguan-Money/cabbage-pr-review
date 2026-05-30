import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createTask,
  fetchExamples,
  fetchLlmModeOptions,
  fetchReviewDepthOptions,
  type ExamplePR,
  type InputType,
  type LlmModeOption,
  type ReviewDepthOption,
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
  const [depthOptions, setDepthOptions] = useState<ReviewDepthOption[]>([]);
  const [selectedDepth, setSelectedDepth] = useState<string>("");
  const [llmOptions, setLlmOptions] = useState<LlmModeOption[]>([]);
  const [selectedLlmMode, setSelectedLlmMode] = useState<string>("");
  const [compressEnabled, setCompressEnabled] = useState(true);
  const [localModel, setLocalModel] = useState("");
  const [localModels, setLocalModels] = useState<string[]>([]);

  useEffect(() => {
    fetchExamples().then(setExamples).catch(() => {});
    fetchReviewDepthOptions()
      .then((data) => {
        setDepthOptions(data.options);
        const def = data.options.find((o) => o.default) ?? data.options[0];
        if (def) setSelectedDepth(def.id);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "无法加载审阅深度选项"));
    fetchLlmModeOptions()
      .then((data) => {
        setLlmOptions(data.options);
        setLocalModels(data.local_models);
        setCompressEnabled(data.default_local_compress_enabled);
        const def = data.options.find((o) => o.default) ?? data.options[0];
        if (def) setSelectedLlmMode(def.id);
        if (data.default_local_model) setLocalModel(data.default_local_model);
        else if (data.local_models[0]) setLocalModel(data.local_models[0]);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "无法加载推理模式选项"));
  }, []);

  const activeDepth = depthOptions.find((o) => o.id === selectedDepth);
  const activeLlm = llmOptions.find((o) => o.id === selectedLlmMode);
  const needsLocal = selectedLlmMode === "hybrid" || selectedLlmMode === "local_only";
  const showCompress = selectedLlmMode === "hybrid" && activeLlm?.compress_toggle;

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      const task = await createTask({
        input_type: tab,
        value,
        project_type: projectType !== "unknown" ? projectType : undefined,
        framework: framework !== "unknown" ? framework : undefined,
        review_depth_mode: selectedDepth || undefined,
        llm_mode: selectedLlmMode || undefined,
        local_compress_enabled: selectedLlmMode === "hybrid" ? compressEnabled : undefined,
        local_model: needsLocal ? localModel || undefined : undefined,
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

  const canSubmit =
    !loading &&
    value.trim() &&
    selectedDepth &&
    selectedLlmMode &&
    (!needsLocal || localModel.trim()) &&
    (activeLlm?.available !== false);

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
        <label>推理模式（任务开始前选择，运行中不可改）</label>
        <div className="card-grid" style={{ marginTop: "0.5rem" }}>
          {llmOptions.map((opt) => (
            <div
              key={opt.id}
              className={`card ${selectedLlmMode === opt.id ? "active" : ""} ${opt.available === false ? "disabled" : ""}`}
              onClick={() => opt.available !== false && setSelectedLlmMode(opt.id)}
              role="button"
              style={opt.available === false ? { opacity: 0.5, pointerEvents: "none" } : undefined}
            >
              <h3>{opt.label}</h3>
              <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{opt.summary}</p>
            </div>
          ))}
        </div>
        {activeLlm && (
          <div style={{ marginTop: "0.75rem", fontSize: "0.9rem", color: "var(--muted)" }}>
            <ul style={{ margin: "0.5rem 0 0 1rem" }}>
              {activeLlm.detail_bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
            {activeLlm.quality_warning && (
              <p className="error" style={{ marginTop: "0.5rem" }}>
                {activeLlm.summary}
              </p>
            )}
          </div>
        )}

        {showCompress && activeLlm?.compress_toggle && (
          <div style={{ marginTop: "1rem" }}>
            <label>
              <input
                type="checkbox"
                checked={compressEnabled}
                onChange={(e) => setCompressEnabled(e.target.checked)}
              />{" "}
              {activeLlm.compress_toggle.label}
            </label>
            {!compressEnabled && (
              <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                {activeLlm.compress_toggle.hint_off}
              </p>
            )}
          </div>
        )}

        {needsLocal && (
          <div style={{ marginTop: "1rem" }}>
            <label>本地模型（Ollama）</label>
            {localModels.length > 0 ? (
              <select value={localModel} onChange={(e) => setLocalModel(e.target.value)}>
                {localModels.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            ) : (
              <input
                value={localModel}
                onChange={(e) => setLocalModel(e.target.value)}
                placeholder="输入本机 Ollama 已安装的模型名"
              />
            )}
          </div>
        )}

        <label style={{ marginTop: "1rem" }}>审阅深度（任务开始前选择，运行中不可改）</label>
        <div className="card-grid" style={{ marginTop: "0.5rem" }}>
          {depthOptions.map((opt) => (
            <div
              key={opt.id}
              className={`card ${selectedDepth === opt.id ? "active" : ""}`}
              onClick={() => setSelectedDepth(opt.id)}
              role="button"
            >
              <h3>{opt.label}</h3>
              <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                {opt.estimated_time} · {opt.cost_tier_label}
              </p>
            </div>
          ))}
        </div>
        {activeDepth && (
          <div style={{ marginTop: "0.75rem", fontSize: "0.9rem", color: "var(--muted)" }}>
            <p>{activeDepth.summary}</p>
            <ul style={{ margin: "0.5rem 0 0 1rem" }}>
              {activeDepth.detail_bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
        )}

        <label style={{ marginTop: "1rem" }}>输入内容</label>
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
        <button onClick={submit} disabled={!canSubmit}>
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
