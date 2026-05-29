export type InputType = "pr_url" | "patch" | "local_path";

export interface AgentProgress {
  agent_id: number;
  name: string;
  status: string;
  message: string;
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
  result?: TaskResult | null;
}

export interface DiffAtom {
  id: string;
  file_path: string;
  change_type: string;
  symbol: string;
  summary: string;
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

export interface DiagramData {
  diagram_type: string;
  mermaid: string;
  nodes: unknown[];
  edges: unknown[];
}

export interface MissingInfoItem {
  module: string;
  reason: string;
  suggestion: string;
}

export interface TaskResult {
  summary: string;
  summary_bullets: string[];
  diagrams: DiagramData[];
  risks: RiskItem[];
  missing_info: MissingInfoItem[];
  degradation_notes: string[];
  diff_atoms: DiffAtom[];
  detected_project_type: string;
  detected_framework: string;
}

export interface ExamplePR {
  id: string;
  title: string;
  pr_url: string;
  description: string;
}

const API = "/api";

export async function createTask(body: {
  input_type: InputType;
  value: string;
  project_type?: string;
  framework?: string;
}): Promise<TaskRecord> {
  const res = await fetch(`${API}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "创建任务失败");
  return res.json();
}

export async function getTask(id: string): Promise<TaskRecord> {
  const res = await fetch(`${API}/tasks/${id}`);
  if (!res.ok) throw new Error("获取任务失败");
  return res.json();
}

export async function getTaskResult(id: string): Promise<TaskResult> {
  const res = await fetch(`${API}/tasks/${id}/result`);
  if (!res.ok) throw new Error("结果尚未就绪");
  return res.json();
}

export async function rerunTask(
  id: string,
  body: { extra_context_paths: string[]; focus_atom_ids: string[] }
): Promise<TaskRecord> {
  const res = await fetch(`${API}/tasks/${id}/rerun`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "重跑失败");
  }
  return res.json();
}

export async function fetchExamples(): Promise<ExamplePR[]> {
  const res = await fetch(`${API}/examples`);
  const data = await res.json();
  return data.examples;
}

export function exportUrl(taskId: string): string {
  return `${API}/tasks/${taskId}/export.md`;
}
