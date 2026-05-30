import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";

import {

  createTask,

  fetchExamples,

  fetchInputPageMeta,

  fetchLlmModeOptions,

  fetchReviewDepthOptions,

  type ExamplePR,

  type InputPageMetaResponse,

  type InputType,

  type LlmModeOption,

  type ReviewDepthOption,

  type LlmAvailabilityHints,

} from "../api/client";

import { pickInitialLlmMode } from "./pickInitialLlmMode";

import {

  isLlmModeRuntimeAvailable,

  needsLocalRuntime,

  resolveUnavailableHint,

} from "./llmModeAvailability";



function MetaLoading() {

  return <div className="meta-loading" aria-busy="true" style={{ minHeight: "4rem" }} />;

}



export default function InputPage() {

  const navigate = useNavigate();

  const [pageMeta, setPageMeta] = useState<InputPageMetaResponse | null>(null);

  const [tab, setTab] = useState<InputType>("pr_url");

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

  const [rulesPreflightEnabled, setRulesPreflightEnabled] = useState(false);

  const [localModel, setLocalModel] = useState("");

  const [localModels, setLocalModels] = useState<string[]>([]);

  const [cloudAvailable, setCloudAvailable] = useState(true);

  const [localAvailable, setLocalAvailable] = useState(false);

  const [availabilityHints, setAvailabilityHints] = useState<LlmAvailabilityHints | null>(null);



  useEffect(() => {

    fetchInputPageMeta()

      .then((meta) => {

        setPageMeta(meta);

        setProjectType(meta.default_project_type);

        setFramework(meta.default_framework);

        if (meta.input_tabs[0]) setTab(meta.input_tabs[0].id);

      })

      .catch((e) => setError(e instanceof Error ? e.message : ""));

    fetchExamples().then(setExamples).catch(() => {});

    fetchReviewDepthOptions()

      .then((data) => {

        setDepthOptions(data.options);

        const def = data.options.find((o) => o.default) ?? data.options[0];

        if (def) setSelectedDepth(def.id);

      })

      .catch((e) => setError(e instanceof Error ? e.message : ""));

    fetchLlmModeOptions()

      .then((data) => {

        setLlmOptions(data.options);

        setLocalModels(data.local_models);

        setCloudAvailable(data.cloud_available);

        setLocalAvailable(data.local_available);

        setAvailabilityHints(data.availability_hints);

        setCompressEnabled(data.default_local_compress_enabled);

        setRulesPreflightEnabled(data.default_rules_preflight_enabled ?? false);

        setSelectedLlmMode(

          pickInitialLlmMode(data.options, {

            cloudAvailable: data.cloud_available,

            localAvailable: data.local_available,

            defaultCompressEnabled: data.default_local_compress_enabled,

          }),

        );

        if (data.default_local_model) setLocalModel(data.default_local_model);

        else if (data.local_models[0]) setLocalModel(data.local_models[0]);

      })

      .catch((e) => setError(e instanceof Error ? e.message : ""));

  }, []);



  const ui = pageMeta?.ui_strings;

  const tabs = pageMeta?.input_tabs ?? [];



  const activeDepth = depthOptions.find((o) => o.id === selectedDepth);

  const activeLlm = llmOptions.find((o) => o.id === selectedLlmMode);

  const needsLocal = activeLlm ? needsLocalRuntime(activeLlm, compressEnabled) : false;

  const showCompress = Boolean(activeLlm?.compress_toggle);

  const showRulesPreflight = Boolean(activeLlm?.rules_preflight_toggle);

  const showDepth = activeLlm?.requires_llm !== false;

  const modeRuntimeAvailable = activeLlm

    ? isLlmModeRuntimeAvailable(activeLlm, cloudAvailable, localAvailable, compressEnabled)

    : false;

  const unavailableHint = activeLlm

    ? resolveUnavailableHint(

        activeLlm,

        availabilityHints,

        cloudAvailable,

        localAvailable,

        compressEnabled,

        localModel,

      )

    : null;



  const submit = async () => {

    if (!ui) return;

    setLoading(true);

    setError("");

    try {

      const task = await createTask({

        input_type: tab,

        value,

        project_type: projectType !== pageMeta?.default_project_type ? projectType : undefined,

        framework: framework !== pageMeta?.default_framework ? framework : undefined,

        review_depth_mode: showDepth ? selectedDepth || undefined : undefined,

        llm_mode: selectedLlmMode || undefined,

        local_compress_enabled: showCompress ? compressEnabled : undefined,

        rules_preflight_enabled: showRulesPreflight ? rulesPreflightEnabled : undefined,

        local_model: needsLocal ? localModel || undefined : undefined,

      });

      navigate(`/tasks/${task.id}`);

    } catch (e) {

      setError(e instanceof Error ? e.message : ui.error_submit);

    } finally {

      setLoading(false);

    }

  };



  const canSubmit =

    !loading &&

    value.trim() &&

    (showDepth ? selectedDepth : true) &&

    selectedLlmMode &&

    modeRuntimeAvailable &&

    (!needsLocal || localModel.trim()) &&

    !unavailableHint;



  if (!pageMeta || !ui) {

    return <MetaLoading />;

  }



  const activeTab = tabs.find((x) => x.id === tab);
  const activeTabHint = activeTab ? activeTab.hint : "";



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

        <label>{ui.llm_mode_label}</label>

        <div className="card-grid" style={{ marginTop: "0.5rem" }}>

          {llmOptions.map((opt) => {

            const optRuntimeAvailable = isLlmModeRuntimeAvailable(

              opt,

              cloudAvailable,

              localAvailable,

              compressEnabled,

            );

            return (

              <div

                key={opt.id}

                className={`card ${selectedLlmMode === opt.id ? "active" : ""} ${!optRuntimeAvailable ? "disabled" : ""}`}

                onClick={() => setSelectedLlmMode(opt.id)}

                role="button"

                style={!optRuntimeAvailable ? { opacity: 0.65 } : undefined}

              >

                <h3>{opt.label}</h3>

                <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{opt.summary}</p>

              </div>

            );

          })}

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



        {showRulesPreflight && activeLlm?.rules_preflight_toggle && (
          <div style={{ marginTop: "1rem" }}>
            <label>
              <input
                type="checkbox"
                checked={rulesPreflightEnabled}
                onChange={(e) => setRulesPreflightEnabled(e.target.checked)}
              />{" "}
              {activeLlm.rules_preflight_toggle.label}
            </label>
            {!rulesPreflightEnabled && (
              <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                {activeLlm.rules_preflight_toggle.hint_off}
              </p>
            )}
          </div>
        )}



        {needsLocal && (

          <div style={{ marginTop: "1rem" }}>

            <label>{ui.local_model_label}</label>

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

                placeholder={ui.local_model_placeholder}

              />

            )}

          </div>

        )}



        {showDepth && (

          <>

            <label style={{ marginTop: "1rem" }}>{ui.review_depth_label}</label>

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

          </>

        )}



        <label style={{ marginTop: "1rem" }}>{ui.input_content_label}</label>

        {tab === "patch" ? (

          <textarea

            value={value}

            onChange={(e) => setValue(e.target.value)}

            rows={8}

            placeholder={ui.patch_placeholder}

          />

        ) : (

          <input value={value} onChange={(e) => setValue(e.target.value)} placeholder={activeTabHint} />

        )}



        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>

          <div>

            <label>{ui.project_type_label}</label>

            <select value={projectType} onChange={(e) => setProjectType(e.target.value)}>

              {pageMeta.project_types.map((p) => (

                <option key={p.id} value={p.id}>

                  {p.label}

                </option>

              ))}

            </select>

          </div>

          <div>

            <label>{ui.framework_label}</label>

            <select value={framework} onChange={(e) => setFramework(e.target.value)}>

              {pageMeta.frameworks.map((f) => (

                <option key={f.id} value={f.id}>

                  {f.label}

                </option>

              ))}

            </select>

          </div>

        </div>



        {error && <div className="error">{error}</div>}

        {unavailableHint && (

          <p className="error" style={{ fontSize: "0.9rem" }}>

            {unavailableHint}

          </p>

        )}

        <button onClick={submit} disabled={!canSubmit}>

          {loading ? ui.submit_loading : ui.submit_idle}

        </button>

      </div>



      <div className="examples card">

        <h3>{ui.examples_heading}</h3>

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

