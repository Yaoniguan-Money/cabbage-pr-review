import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  fetchProviderPresets,
  fetchRuntimeConfigMeta,
  fetchRuntimeConfigPreview,
  type ProviderPreset,
  type RuntimeConfigMetaResponse,
  type RuntimeConfigPreviewResponse,
} from "../api/client";
import {
  clearRuntimeCredentials,
  isCloudCredentialsEnabled,
  isGithubCredentialsEnabled,
  loadRuntimeCredentials,
  prepareCredentialsForSave,
  saveRuntimeCredentials,
  toApiPayload,
  type StoredRuntimeCredentials,
} from "../utils/runtimeCredentialsStorage";

type Props = {
  value: StoredRuntimeCredentials;
  onChange: (next: StoredRuntimeCredentials) => void;
  onSaved?: () => void;
  onPreviewChange?: (preview: RuntimeConfigPreviewResponse) => void;
};

function previewSignature(creds: StoredRuntimeCredentials): string {
  return JSON.stringify({
    enable_cloud: creds.enable_cloud,
    enable_github: creds.enable_github,
    payload: toApiPayload(creds) ?? null,
  });
}

export default function RuntimeCredentialsPanel({
  value,
  onChange,
  onSaved,
  onPreviewChange,
}: Props) {
  const [meta, setMeta] = useState<RuntimeConfigMetaResponse | null>(null);
  const [presets, setPresets] = useState<ProviderPreset[]>([]);
  const [presetId, setPresetId] = useState("deepseek");
  const [open, setOpen] = useState(false);
  const [savedHint, setSavedHint] = useState(false);
  const [preview, setPreview] = useState<RuntimeConfigPreviewResponse | null>(null);
  const lastSignatureRef = useRef<string>("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onPreviewChangeRef = useRef(onPreviewChange);
  onPreviewChangeRef.current = onPreviewChange;

  const refreshPreview = useCallback(async (creds: StoredRuntimeCredentials, signature: string) => {
    if (signature === lastSignatureRef.current) {
      return;
    }
    try {
      const result = await fetchRuntimeConfigPreview(toApiPayload(creds));
      lastSignatureRef.current = signature;
      setPreview(result);
      onPreviewChangeRef.current?.(result);
    } catch {
      setPreview(null);
    }
  }, []);

  useEffect(() => {
    fetchRuntimeConfigMeta()
      .then((m) => {
        setMeta(m);
        if (m.expand_panel_default) setOpen(true);
      })
      .catch(() => {});
    fetchProviderPresets()
      .then((d) => setPresets(d.presets))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!meta?.allow_runtime_credentials) return;
    const signature = previewSignature(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void refreshPreview(value, signature);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, meta?.allow_runtime_credentials, refreshPreview]);

  const ui = meta?.ui_strings ?? {};
  const isPublic = meta?.is_public_deploy ?? false;

  const statusLines = useMemo(() => {
    const cloud = (() => {
      if (isPublic) {
        if (preview?.cloud_available && isCloudCredentialsEnabled(value)) {
          return ui.status_cloud_ready;
        }
        return ui.status_cloud_public ?? ui.status_cloud_off;
      }
      if (preview?.server_cloud_configured) return ui.status_cloud_server;
      if (preview?.cloud_available && isCloudCredentialsEnabled(value)) {
        return ui.status_cloud_ready;
      }
      if (value.enable_cloud && !isCloudCredentialsEnabled(value)) {
        return ui.status_cloud_off;
      }
      if (preview?.cloud_available) return ui.status_cloud_ready;
      return ui.status_cloud_off;
    })();

    const github = (() => {
      if (isPublic) {
        if (preview?.github_token_configured && isGithubCredentialsEnabled(value)) {
          return ui.status_github_ready;
        }
        return ui.status_github_public ?? ui.status_github_off;
      }
      if (preview?.server_github_configured) return ui.status_github_server;
      if (preview?.github_token_configured && isGithubCredentialsEnabled(value)) {
        return ui.status_github_ready;
      }
      if (value.enable_github && !isGithubCredentialsEnabled(value)) {
        return ui.status_github_off;
      }
      if (preview?.github_token_configured) return ui.status_github_ready;
      return ui.status_github_off;
    })();

    const local = preview?.local_available ? ui.status_local_ready : ui.status_local_off;

    return { cloud, github, local };
  }, [isPublic, preview, ui, value]);

  const applyPreset = (id: string) => {
    setPresetId(id);
    const p = presets.find((x) => x.id === id);
    if (!p || id === "custom") return;
    onChange({
      ...value,
      enable_cloud: true,
      cloud_api_base: p.api_base,
      cloud_flash_model: p.flash_model,
      cloud_pro_model: p.pro_model,
    });
    setOpen(true);
  };

  const handleSave = () => {
    const prepared = prepareCredentialsForSave(value);
    saveRuntimeCredentials(prepared);
    onChange(prepared);
    setSavedHint(true);
    onSaved?.();
    lastSignatureRef.current = "";
    void refreshPreview(prepared, previewSignature(prepared));
    window.setTimeout(() => setSavedHint(false), 4000);
  };

  const handleClear = () => {
    clearRuntimeCredentials();
    const cleared = loadRuntimeCredentials();
    onChange(cleared);
    onSaved?.();
    lastSignatureRef.current = "";
    void refreshPreview(cleared, previewSignature(cleared));
  };

  const setEnableCloud = (enabled: boolean) => {
    onChange({ ...value, enable_cloud: enabled });
    if (enabled) setOpen(true);
  };

  const setEnableGithub = (enabled: boolean) => {
    onChange({ ...value, enable_github: enabled });
    if (enabled) setOpen(true);
  };

  if (!meta?.allow_runtime_credentials) return null;

  return (
    <section className="card runtime-credentials-panel">
      <div className="runtime-credentials-toggles">
        <label className="runtime-toggle-row">
          <input
            type="checkbox"
            className="runtime-toggle-input"
            checked={value.enable_cloud}
            onChange={(e) => setEnableCloud(e.target.checked)}
          />
          <span className="runtime-toggle-switch" aria-hidden="true" />
          <span className="runtime-toggle-text">{ui.toggle_cloud_label}</span>
        </label>
        <p className="runtime-status-line" role="status">
          {statusLines.cloud}
        </p>
        <label className="runtime-toggle-row">
          <input
            type="checkbox"
            className="runtime-toggle-input"
            checked={value.enable_github}
            onChange={(e) => setEnableGithub(e.target.checked)}
          />
          <span className="runtime-toggle-switch" aria-hidden="true" />
          <span className="runtime-toggle-text">{ui.toggle_github_label}</span>
        </label>
        <p className="runtime-status-line" role="status">
          {statusLines.github}
        </p>
        <p className="runtime-status-line runtime-status-line--muted" role="status">
          {statusLines.local}
        </p>
      </div>
      <button
        type="button"
        className="runtime-credentials-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {ui.panel_title ?? "API 与 GitHub 设置"}
      </button>
      {savedHint && ui.saved_hint ? (
        <p className="runtime-saved-banner" role="status">
          {ui.saved_hint}
        </p>
      ) : null}
      {open ? (
        <div className="runtime-credentials-body">
          {ui.panel_summary ? <p className="section-hint">{ui.panel_summary}</p> : null}
          <label className="field-label">
            {ui.preset_label ?? "厂商预设"}
            <select
              value={presetId}
              onChange={(e) => applyPreset(e.target.value)}
              className="field-input"
              disabled={!value.enable_cloud}
            >
              {presets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field-label">
            {ui.api_base_label ?? "API Base URL"}
            <input
              className="field-input"
              value={value.cloud_api_base}
              onChange={(e) => onChange({ ...value, cloud_api_base: e.target.value })}
              placeholder="https://api.deepseek.com"
              disabled={!value.enable_cloud}
            />
          </label>
          <label className="field-label">
            {ui.api_key_label ?? "云端 API Key"}
            <input
              className="field-input"
              type="password"
              autoComplete="off"
              value={value.cloud_api_key}
              onChange={(e) => onChange({ ...value, cloud_api_key: e.target.value })}
              disabled={!value.enable_cloud}
            />
          </label>
          <label className="field-label">
            {ui.flash_model_label ?? "Flash 模型"}
            <input
              className="field-input"
              value={value.cloud_flash_model}
              onChange={(e) => onChange({ ...value, cloud_flash_model: e.target.value })}
              disabled={!value.enable_cloud}
            />
          </label>
          <label className="field-label">
            {ui.pro_model_label ?? "Pro 模型"}
            <input
              className="field-input"
              value={value.cloud_pro_model}
              onChange={(e) => onChange({ ...value, cloud_pro_model: e.target.value })}
              disabled={!value.enable_cloud}
            />
          </label>
          <label className="field-label">
            {ui.github_token_label ?? "GitHub Token"}
            <input
              className="field-input"
              type="password"
              autoComplete="off"
              value={value.github_token}
              onChange={(e) => onChange({ ...value, github_token: e.target.value })}
              disabled={!value.enable_github}
            />
          </label>
          <div className="runtime-credentials-actions">
            <button type="button" className="btn secondary" onClick={handleSave}>
              {ui.save_local_button ?? "保存到本机"}
            </button>
            <button type="button" className="btn secondary" onClick={handleClear}>
              {ui.clear_button ?? "清除凭据"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
