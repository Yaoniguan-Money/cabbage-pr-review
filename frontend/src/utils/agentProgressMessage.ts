import type { AgentProgress } from "../api/client";

/** 并行扫描阶段（≥2 路同 parallel_group 且均为 running）时使用 meta 提示文案。 */
export function resolveRunningMessage(
  progress: AgentProgress[] | undefined,
  detailUi: Record<string, string>,
  fallback: string,
): string {
  if (!progress?.length) {
    return fallback;
  }
  const running = progress.filter((a) => a.status === "running");
  if (running.length >= 2) {
    const groups = new Set(
      running.map((a) => a.parallel_group).filter((g): g is string => Boolean(g)),
    );
    if (groups.size === 1) {
      return detailUi.parallel_running_hint?.trim() || fallback;
    }
  }
  const first = running[0];
  return first?.message?.trim() || fallback;
}
