import { formatTemplate } from "../utils/formatTemplate";
import { parseContentDispositionFilename } from "../utils/parseContentDispositionFilename";

export type InputType = "pr_url" | "patch" | "local_path";

export interface AgentProgress {
  agent_id: number;
  name: string;
  status: string;
  message: string;
  parallel_group?: string | null;
}

export interface ReviewStats {
  review_depth_mode: string;
  review_depth_label: string;
  total_atoms: number;
  reviewed_atoms: number;
  batches_run: number;
  pro_calls: number;
  flash_calls: number;
}

export interface ReviewDepthOption {
  id: string;
  label: string;
  summary: string;
  detail_bullets: string[];
  estimated_time: string;
  cost_tier: "low" | "medium" | "high";
  cost_tier_label: string;
  default: boolean;
}

export interface LlmModeCompressToggle {
  default_enabled: boolean;
  label: string;
  hint_off: string;
}

export interface LlmAvailabilityHints {
  cloud_unavailable: string;
  local_unavailable: string;
  local_for_compress: string;
  compress_model_required: string;
  local_model_required: string;
}

export interface LlmModeOption {
  id: string;
  label: string;
  summary: string;
  detail_bullets: string[];
  requires_cloud: boolean;
  requires_local: boolean;
  requires_llm: boolean;
  quality_warning: boolean;
  visualization_mode: "diagrams" | "markdown";
  rerun_supported: boolean;
  hide_token_stats: boolean;
  default: boolean;
  available: boolean;
  unavailable_hint?: string | null;
  compress_toggle?: LlmModeCompressToggle;
}

export interface PrPatchFile {
  filename: string;
  status: string;
  patch: string;
  additions?: number;
  deletions?: number;
}

export interface PrContext {
  title?: string;
  html_url?: string;
  base_ref?: string;
  head_ref?: string;
  owner?: string;
  repo?: string;
  number?: number;
  patches?: PrPatchFile[];
  file_paths?: string[];
  changed_files_count?: number;
}

export interface TaskRecord {
  id: string;
  input_type: InputType;
  input_value: string;
  status: string;
  current_agent: number;
  agent_progress: AgentProgress[];
  project_type?: string | null;
  framework?: string | null;
  error_message?: string | null;
  rerun_used: boolean;
  review_depth_mode?: string;
  review_depth_label?: string;
  llm_mode?: string;
  llm_mode_label?: string;
  visualization_mode?: "diagrams" | "markdown";
  rerun_supported?: boolean;
  local_compress_enabled?: boolean;
  local_model?: string;
  pr_context?: PrContext;
  demo_scenario_id?: string | null;
  expected_rule_ids?: string[];
  compress_stats?: {
    compress_calls: number;
    chars_before: number;
    chars_after: number;
  } | null;
  token_stats?: {
    cloud_prompt_tokens: number;
    cloud_completion_tokens: number;
    cloud_total_tokens: number;
    local_prompt_tokens: number;
    local_completion_tokens: number;
    local_total_tokens: number;
    total_tokens: number;
    estimated: boolean;
    display_segments: Array<{
      key: string;
      label: string;
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    }>;
  } | null;
  result?: TaskResult | null;
}

export interface DiffAtom {
  id: string;
  file_path: string;
  change_type: string;
  symbol: string;
  summary: string;
  patch_excerpt?: string;
  hunk_patch?: string;
  added_line_count?: number;
  removed_line_count?: number;
}

export interface RiskItem {
  id: string;
  title: string;
  description: string;
  risk_level: "high" | "medium" | "low";
  confidence: "high" | "medium" | "low";
  evidence?: string;
  suggestion?: string;
  related_atoms: string[];
  file_paths: string[];
}

export interface DiagramLegendItem {
  key: string;
  label: string;
  color: string;
}

export interface DiagramUiStrings {
  render_error_title: string;
  render_error_hint: string;
  unnamed_node: string;
  empty_structure: string;
  node_summary_label: string;
  node_risk_prefix: string;
  node_confidence_prefix: string;
}

export interface DiagramTypeMeta {
  id: string;
  default_title: string;
  description: string;
  layout: string;
}

export interface DiagramMetaResponse {
  section_label: string;
  section_preview_label: string;
  empty_diagrams: string;
  diagram_count?: number;
  overview_risk_preview_count?: number;
  ui_strings: DiagramUiStrings;
  default_legend: DiagramLegendItem[];
  diagram_types: DiagramTypeMeta[];
}

export interface DiagramData {
  diagram_type: string;
  title?: string;
  caption?: string;
  legend?: DiagramLegendItem[];
  mermaid: string;
  nodes: unknown[];
  edges: unknown[];
}

export interface MissingInfoItem {
  module: string;
  reason: string;
  suggestion: string;
}

export interface RuleHitRecord {
  rule_id: string;
  severity: string;
  file_path: string;
  evidence: string;
  message: string;
}

export interface ProjectIndex {
  version?: string;
  modules?: string[];
  routes?: string[];
  entry_files?: string[];
  directory_tree?: string[];
  raw_summary?: string;
}

export interface TaskResult {
  summary: string;
  summary_bullets: string[];
  diagrams: DiagramData[];
  risks: RiskItem[];
  missing_info: MissingInfoItem[];
  degradation_notes: string[];
  diff_atoms: DiffAtom[];
  base_index?: ProjectIndex | null;
  head_index?: ProjectIndex | null;
  detected_project_type: string;
  detected_framework: string;
  review_stats?: ReviewStats | null;
  markdown_report?: string;
  rule_hits?: RuleHitRecord[];
}

export interface ExamplePR {
  id: string;
  title: string;
  pr_url: string;
  description: string;
}

export interface ClientMetaResponse {
  error_messages: Record<string, string>;
  use_mock_llm?: boolean;
  mock_mode_banner?: string;
  cloud_unavailable_banner?: string;
}

export interface RuntimeCredentialsPayload {
  cloud_api_base?: string;
  cloud_api_key?: string;
  cloud_flash_model?: string;
  cloud_pro_model?: string;
  github_token?: string;
}

export interface RuntimeConfigMetaResponse {
  allow_runtime_credentials: boolean;
  deploy_mode: string;
  is_public_deploy: boolean;
  server_cloud_configured: boolean;
  server_github_configured: boolean;
  expand_panel_default: boolean;
  ui_strings: Record<string, string>;
}

export interface RuntimeConfigPreviewResponse {
  cloud_available: boolean;
  github_token_configured: boolean;
  local_available: boolean;
  server_cloud_configured: boolean;
  server_github_configured: boolean;
}

export interface ProviderPreset {
  id: string;
  label: string;
  api_base: string;
  flash_model: string;
  pro_model: string;
}

export interface DemoPatchScenario {
  id: string;
  title: string;
  description: string;
  expected_rule_ids: string[];
  patch_text: string;
}

export interface RulesCatalogEntry {
  id: string;
  message: string;
  severity: string;
  matcher_type?: string;
}

export interface RulesCatalogResponse {
  rules_count: number;
  rules_invalid_count: number;
  rules_pack_version?: string;
  rules: RulesCatalogEntry[];
}

export interface InputPageTabMeta {
  id: InputType;
  title: string;
  hint: string;
}

export interface InputPageSelectOption {
  id: string;
  label: string;
}

export interface UsageGuideSection {
  id: string;
  heading: string;
  paragraphs: string[];
}

export interface UsageGuideMeta {
  title: string;
  toggle_show: string;
  toggle_hide: string;
  default_expanded: boolean;
  sections: UsageGuideSection[];
}

export interface InputPageMetaResponse {
  default_project_type: string;
  default_framework: string;
  project_types: InputPageSelectOption[];
  frameworks: InputPageSelectOption[];
  input_tabs: InputPageTabMeta[];
  ui_strings: Record<string, string>;
  usage_guide?: UsageGuideMeta;
  is_public_deploy?: boolean;
}

export interface RulesMetaResponse {
  rules_pack_version: string;
  visualization_mode: string;
  ui_strings: Record<string, string>;
  table_change_headers: string[];
  table_hit_headers: string[];
  group_by_rule_id_default?: boolean;
  collapse_low_default?: boolean;
}

export interface DetailPageMetaResponse {
  ui_strings: Record<string, string>;
  export_blob_revoke_delay_ms: number;
}

const API = "/api";

let clientMetaCache: ClientMetaResponse | null = null;
let clientMetaPromise: Promise<ClientMetaResponse> | null = null;

export async function fetchClientMeta(): Promise<ClientMetaResponse> {
  if (clientMetaCache) return clientMetaCache;
  if (!clientMetaPromise) {
    clientMetaPromise = fetch(`${API}/client-meta`)
      .then(async (res) => {
        if (!res.ok) throw new Error("fetch_client_meta");
        return res.json() as Promise<ClientMetaResponse>;
      })
      .then((data) => {
        clientMetaCache = data;
        return data;
      });
  }
  return clientMetaPromise;
}

async function resolveClientError(key: string, detail?: string): Promise<string> {
  if (detail) return detail;
  try {
    const meta = await fetchClientMeta();
    return meta.error_messages[key] || key;
  } catch {
    return key;
  }
}

async function throwApiError(res: Response, key: string): Promise<never> {
  let detail: string | undefined;
  try {
    const data = await res.json();
    if (typeof data.detail === "string") detail = data.detail;
  } catch {
    /* ignore */
  }
  throw new Error(await resolveClientError(key, detail));
}

export async function createTask(body: {
  input_type: InputType;
  value: string;
  project_type?: string;
  framework?: string;
  review_depth_mode?: string;
  llm_mode?: string;
  local_compress_enabled?: boolean;
  local_model?: string;
  cloud_flash_model?: string;
  cloud_pro_model?: string;
  demo_scenario_id?: string;
  runtime_credentials?: RuntimeCredentialsPayload;
}): Promise<TaskRecord> {
  const res = await fetch(`${API}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) await throwApiError(res, "create_task");
  return res.json();
}

export async function getTask(id: string): Promise<TaskRecord> {
  const res = await fetch(`${API}/tasks/${id}`);
  if (!res.ok) await throwApiError(res, "get_task");
  return res.json();
}

export async function getTaskResult(id: string): Promise<TaskResult> {
  const res = await fetch(`${API}/tasks/${id}/result`);
  if (!res.ok) await throwApiError(res, "get_task_result");
  return res.json();
}

export async function rerunTask(
  id: string,
  body: {
    extra_context_paths: string[];
    focus_atom_ids: string[];
    runtime_credentials?: RuntimeCredentialsPayload;
  }
): Promise<TaskRecord> {
  const res = await fetch(`${API}/tasks/${id}/rerun`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) await throwApiError(res, "rerun_task");
  return res.json();
}

export async function fetchReviewDepthOptions(): Promise<{
  options: ReviewDepthOption[];
  default_review_depth_mode: string;
}> {
  const res = await fetch(`${API}/review-depth-options`);
  if (!res.ok) await throwApiError(res, "fetch_review_depth");
  return res.json();
}

export async function fetchLlmModeOptions(hasRuntimeCloudKey = false): Promise<{
  options: LlmModeOption[];
  default_llm_mode: string;
  default_local_compress_enabled: boolean;
  cloud_available: boolean;
  local_available: boolean;
  local_models: string[];
  default_local_model: string;
  availability_hints: LlmAvailabilityHints;
}> {
  const q = hasRuntimeCloudKey ? "?has_runtime_cloud_key=true" : "";
  const res = await fetch(`${API}/llm-mode-options${q}`);
  if (!res.ok) await throwApiError(res, "fetch_llm_mode");
  return res.json();
}

export async function fetchRuntimeConfigMeta(): Promise<RuntimeConfigMetaResponse> {
  const res = await fetch(`${API}/runtime-config-meta`);
  if (!res.ok) throw new Error("fetch_runtime_config_meta");
  return res.json();
}

export async function fetchProviderPresets(): Promise<{ presets: ProviderPreset[] }> {
  const res = await fetch(`${API}/provider-presets`);
  if (!res.ok) throw new Error("fetch_provider_presets");
  return res.json();
}

export async function fetchRuntimeConfigPreview(
  runtime_credentials?: RuntimeCredentialsPayload,
): Promise<RuntimeConfigPreviewResponse> {
  const res = await fetch(`${API}/runtime-config/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ runtime_credentials: runtime_credentials ?? null }),
  });
  if (!res.ok) throw new Error("fetch_runtime_config_preview");
  return res.json();
}

export async function fetchDetailPageMeta(): Promise<DetailPageMetaResponse> {
  const res = await fetch(`${API}/detail-page-meta`);
  if (!res.ok) await throwApiError(res, "fetch_detail_page_meta");
  return res.json();
}

export async function fetchRulesMeta(): Promise<RulesMetaResponse> {
  const res = await fetch(`${API}/rules-meta`);
  if (!res.ok) await throwApiError(res, "fetch_rules_meta");
  return res.json();
}

export async function fetchDiagramMeta(): Promise<DiagramMetaResponse> {
  const res = await fetch(`${API}/diagram-meta`);
  if (!res.ok) await throwApiError(res, "fetch_diagram_meta");
  return res.json();
}

export async function fetchInputPageMeta(): Promise<InputPageMetaResponse> {
  const res = await fetch(`${API}/input-page-meta`);
  if (!res.ok) await throwApiError(res, "fetch_input_page_meta");
  return res.json();
}

export async function fetchExamples(): Promise<ExamplePR[]> {
  const res = await fetch(`${API}/examples`);
  const data = await res.json();
  return data.examples;
}

export async function fetchDemoPatches(): Promise<DemoPatchScenario[]> {
  const res = await fetch(`${API}/demo-patches`);
  if (!res.ok) await throwApiError(res, "fetch_demo_patches");
  const data = await res.json();
  return data.scenarios;
}

export async function fetchRulesCatalog(): Promise<RulesCatalogResponse> {
  const res = await fetch(`${API}/rules-catalog`);
  if (!res.ok) await throwApiError(res, "fetch_rules_catalog");
  return res.json();
}

export function exportUrl(taskId: string): string {
  return `${API}/tasks/${taskId}/export.md`;
}

export async function downloadExportMarkdown(
  taskId: string,
  filenameTemplate: string,
  revokeDelayMs: number,
  emptyBlobMessage: string,
): Promise<void> {
  const res = await fetch(exportUrl(taskId));
  if (!res.ok) await throwApiError(res, "export_markdown");
  const blob = await res.blob();
  if (blob.size === 0) {
    throw new Error(emptyBlobMessage);
  }
  const fromHeader = parseContentDispositionFilename(res.headers.get("Content-Disposition"));
  const filename =
    fromHeader ?? formatTemplate(filenameTemplate, { task_id: taskId });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), revokeDelayMs);
}

/** 测试用：重置 client meta 缓存 */
export function resetClientMetaCache(): void {
  clientMetaCache = null;
  clientMetaPromise = null;
}
