import { useCallback, useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";

import {

  createTask,

  fetchDemoPatches,

  fetchExamples,

  fetchInputPageMeta,

  fetchLlmModeOptions,

  fetchReviewDepthOptions,

  fetchRulesCatalog,

  fetchClientMeta,

  type DemoPatchScenario,

  type ExamplePR,

  type InputPageMetaResponse,

  type InputType,

  type LlmModeOption,

  type ReviewDepthOption,

  type LlmAvailabilityHints,

  type RulesCatalogResponse,

} from "../api/client";

import RuntimeCredentialsPanel from "../components/RuntimeCredentialsPanel";
import UsageGuidePanel from "../components/UsageGuidePanel";
import { RevealStagger, RevealStaggerItem } from "../components/motion/Reveal";
import {
  isCloudCredentialsEnabled,
  loadRuntimeCredentials,
  toApiPayload,
  type StoredRuntimeCredentials,
} from "../utils/runtimeCredentialsStorage";
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

  const [demoPatches, setDemoPatches] = useState<DemoPatchScenario[]>([]);
  const [selectedDemoScenarioId, setSelectedDemoScenarioId] = useState<string | null>(null);
  const [demoPatchesError, setDemoPatchesError] = useState("");

  const [rulesCatalog, setRulesCatalog] = useState<RulesCatalogResponse | null>(null);

  const [rulesCatalogOpen, setRulesCatalogOpen] = useState(false);

  const [depthOptions, setDepthOptions] = useState<ReviewDepthOption[]>([]);

  const [selectedDepth, setSelectedDepth] = useState<string>("");

  const [llmOptions, setLlmOptions] = useState<LlmModeOption[]>([]);

  const [selectedLlmMode, setSelectedLlmMode] = useState<string>("");

  const [compressEnabled, setCompressEnabled] = useState(true);

  const [localModel, setLocalModel] = useState("");

  const [localModels, setLocalModels] = useState<string[]>([]);

  const [cloudAvailable, setCloudAvailable] = useState(true);

  const [localAvailable, setLocalAvailable] = useState(false);

  const [availabilityHints, setAvailabilityHints] = useState<LlmAvailabilityHints | null>(null);

  const [cloudUnavailableBanner, setCloudUnavailableBanner] = useState("");

  const [runtimeCreds, setRuntimeCreds] = useState<StoredRuntimeCredentials>(() =>
    loadRuntimeCredentials(),
  );

  const applyLlmOptions = useCallback((hasKey: boolean) => {
    fetchLlmModeOptions(hasKey)
      .then((data) => {
        setLlmOptions(data.options);
        setLocalModels(data.local_models);
        setCloudAvailable(data.cloud_available);
        setLocalAvailable(data.local_available);
        setAvailabilityHints(data.availability_hints);
        setCompressEnabled(data.default_local_compress_enabled);
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

  const handlePreviewChange = useCallback(
    (preview: { cloud_available: boolean }) => {
      applyLlmOptions(preview.cloud_available);
    },
    [applyLlmOptions],
  );

  useEffect(() => {

    fetchClientMeta()
      .then((meta) => {
        if (meta.cloud_unavailable_banner?.trim()) {
          setCloudUnavailableBanner(meta.cloud_unavailable_banner.trim());
        }
      })
      .catch(() => {});

    fetchInputPageMeta()

      .then((meta) => {

        setPageMeta(meta);

        setProjectType(meta.default_project_type);

        setFramework(meta.default_framework);

        if (meta.input_tabs[0]) setTab(meta.input_tabs[0].id);

      })

      .catch((e) => setError(e instanceof Error ? e.message : ""));

    fetchExamples().then(setExamples).catch(() => {});

    fetchDemoPatches()
      .then((scenarios) => {
        setDemoPatches(scenarios);
        setDemoPatchesError("");
      })
      .catch((e) => {
        setDemoPatches([]);
        setDemoPatchesError(e instanceof Error ? e.message : "");
      });

    fetchRulesCatalog().then(setRulesCatalog).catch(() => {});

    fetchReviewDepthOptions()

      .then((data) => {

        setDepthOptions(data.options);

        const def = data.options.find((o) => o.default) ?? data.options[0];

        if (def) setSelectedDepth(def.id);

      })

      .catch((e) => setError(e instanceof Error ? e.message : ""));

    applyLlmOptions(isCloudCredentialsEnabled(runtimeCreds));

  }, []);



  const ui = pageMeta?.ui_strings;

  const tabs = pageMeta?.input_tabs ?? [];



  const activeDepth = depthOptions.find((o) => o.id === selectedDepth);

  const activeLlm = llmOptions.find((o) => o.id === selectedLlmMode);

  const needsLocal = activeLlm ? needsLocalRuntime(activeLlm, compressEnabled) : false;

  const showCompress = Boolean(activeLlm?.compress_toggle);

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

      const credsPayload = toApiPayload(runtimeCreds);
      const task = await createTask({

        input_type: tab,

        value,

        project_type: projectType !== pageMeta?.default_project_type ? projectType : undefined,

        framework: framework !== pageMeta?.default_framework ? framework : undefined,

        review_depth_mode: showDepth ? selectedDepth || undefined : undefined,

        llm_mode: selectedLlmMode || undefined,

        local_compress_enabled: showCompress ? compressEnabled : undefined,

        local_model: needsLocal ? localModel || undefined : undefined,
        cloud_flash_model: runtimeCreds.cloud_flash_model.trim() || undefined,
        cloud_pro_model: runtimeCreds.cloud_pro_model.trim() || undefined,
        demo_scenario_id: selectedDemoScenarioId || undefined,
        runtime_credentials: credsPayload,
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



  const loadDemoScenario = (scenario: DemoPatchScenario) => {
    setTab("patch");
    setValue(scenario.patch_text);
    setSelectedDemoScenarioId(scenario.id);
    const rulesOnly = llmOptions.find((o) => o.id === "rules_only" && o.available !== false);
    if (rulesOnly) {
      setSelectedLlmMode(rulesOnly.id);
    }
  };

  return (
    <div className="input-page">
      {ui.credentials_warm_tips_title && ui.credentials_warm_tips_body ? (
        <div className="warm-tips-banner" role="note">
          <strong className="warm-tips-title">{ui.credentials_warm_tips_title}</strong>
          <p className="warm-tips-body">{ui.credentials_warm_tips_body}</p>
        </div>
      ) : null}
      <UsageGuidePanel guide={pageMeta?.usage_guide} />
      {cloudUnavailableBanner ? (
        <div className="risk-item medium alert-banner" role="status">
          {cloudUnavailableBanner}
        </div>
      ) : null}
      <RuntimeCredentialsPanel
        value={runtimeCreds}
        onChange={(next) => {
          setRuntimeCreds(next);
          applyLlmOptions(isCloudCredentialsEnabled(next));
        }}
        onSaved={() => {
          const c = loadRuntimeCredentials();
          setRuntimeCreds(c);
          applyLlmOptions(isCloudCredentialsEnabled(c));
        }}
        onPreviewChange={handlePreviewChange}
      />
      {(demoPatches.length > 0 || demoPatchesError) && (
        <section className="demo-hero card" aria-label={ui.demo_patches_heading}>
          <h2 className="demo-hero-title">{ui.demo_patches_heading}</h2>
          {ui.demo_patches_hint ? <p className="section-hint">{ui.demo_patches_hint}</p> : null}
          {ui.demo_step_select ? (
            <div className="demo-hero-steps">
              <span className="demo-step-chip">{ui.demo_step_select}</span>
              <span className="demo-step-chip">{ui.demo_step_mode}</span>
              <span className="demo-step-chip">{ui.demo_step_run}</span>
            </div>
          ) : null}
          {demoPatchesError ? (
            <p className="error">{demoPatchesError || ui.error_load_demo_patches}</p>
          ) : (
            <RevealStagger className="demo-scenario-grid">
              {demoPatches.map((scenario) => (
                <RevealStaggerItem key={scenario.id}>
                <article
                  className={`demo-scenario-card ${selectedDemoScenarioId === scenario.id ? "active" : ""}`}
                >
                  <h3 className="demo-scenario-card-title">{scenario.title}</h3>
                  <p className="demo-scenario-card-desc">{scenario.description}</p>
                  {scenario.expected_rule_ids.length > 0 ? (
                    <div className="demo-scenario-expected">
                      <span className="demo-scenario-expected-label">{ui.demo_scenario_expected}</span>
                      <div className="demo-scenario-badges">
                        {scenario.expected_rule_ids.map((ruleId) => (
                          <span key={ruleId} className="demo-rule-badge">
                            {ruleId}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <button
                    className="secondary demo-scenario-btn"
                    type="button"
                    onClick={() => loadDemoScenario(scenario)}
                  >
                    {ui.demo_scenario_load}
                  </button>
                </article>
                </RevealStaggerItem>
              ))}
            </RevealStagger>
          )}
        </section>
      )}

      <section className="form-section">
        <h2 className="section-label">{ui.input_content_label}</h2>
        <div className="option-list">
          {tabs.map((t) => (
            <div
              key={t.id}
              className={`option-item ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setTab(t.id);
                }
              }}
              role="button"
              tabIndex={0}
            >
              <h3>{t.title}</h3>
              <p>{t.hint}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="form-panel">
        <section className="form-section">
          <h2 className="section-label">{ui.llm_mode_label}</h2>
          <div className="option-list option-list--grid">
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
                  className={`option-item ${selectedLlmMode === opt.id ? "active" : ""} ${!optRuntimeAvailable ? "disabled" : ""}`}
                  onClick={() => setSelectedLlmMode(opt.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedLlmMode(opt.id);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <h3>{opt.label}</h3>
                  <p>{opt.summary}</p>
                </div>
              );
            })}
          </div>
          {activeLlm && (
            <div className="option-detail">
              <ul>
                {activeLlm.detail_bullets.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
              {activeLlm.quality_warning && <p className="error">{activeLlm.summary}</p>}
            </div>
          )}
        </section>

        {showCompress && activeLlm?.compress_toggle && (
          <div className="form-section">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={compressEnabled}
                onChange={(e) => setCompressEnabled(e.target.checked)}
              />
              {activeLlm.compress_toggle.label}
            </label>
            {!compressEnabled && <p className="section-hint">{activeLlm.compress_toggle.hint_off}</p>}
          </div>
        )}

        {needsLocal && (
          <div className="form-section">
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
          <section className="form-section">
            <h2 className="section-label">{ui.review_depth_label}</h2>
            <div className="option-list option-list--grid">
              {depthOptions.map((opt) => (
                <div
                  key={opt.id}
                  className={`option-item ${selectedDepth === opt.id ? "active" : ""}`}
                  onClick={() => setSelectedDepth(opt.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedDepth(opt.id);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <h3>{opt.label}</h3>
                  <p>
                    {opt.estimated_time} · {opt.cost_tier_label}
                  </p>
                </div>
              ))}
            </div>
            {activeDepth && (
              <div className="option-detail">
                <p>{activeDepth.summary}</p>
                <ul>
                  {activeDepth.detail_bullets.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        <section className="form-section">
          <h2 className="section-label">{activeTab?.title ?? ui.input_content_label}</h2>

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



        <div className="field-row">
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
        {unavailableHint && <p className="error">{unavailableHint}</p>}
        <button type="button" className="btn-primary" onClick={submit} disabled={!canSubmit}>
          {loading ? ui.submit_loading : ui.submit_idle}
        </button>
        </section>
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

      {rulesCatalog && ui.rules_catalog_heading && (
        <div className="card">
          <h3>{ui.rules_catalog_heading}</h3>
          <p className="section-hint">
            {(ui.rules_catalog_count_label || "").replace("{count}", String(rulesCatalog.rules_count))}
            {rulesCatalog.rules_invalid_count > 0
              ? ` · ${(ui.rules_catalog_invalid_label || "").replace("{count}", String(rulesCatalog.rules_invalid_count))}`
              : ""}
            {rulesCatalog.rules_pack_version
              ? ` · ${(ui.rules_catalog_version_label || "").replace("{version}", rulesCatalog.rules_pack_version)}`
              : ""}
          </p>
          <button
            type="button"
            className="secondary"
            onClick={() => setRulesCatalogOpen((open) => !open)}
          >
            {rulesCatalogOpen ? ui.rules_catalog_toggle_hide : ui.rules_catalog_toggle_show}
          </button>
          {rulesCatalogOpen && (
            <div className="option-detail">
              <ul>
                {rulesCatalog.rules.map((rule) => (
                  <li key={rule.id}>
                    <strong>{rule.id}</strong> · {rule.severity} — {rule.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

    </div>

  );

}

