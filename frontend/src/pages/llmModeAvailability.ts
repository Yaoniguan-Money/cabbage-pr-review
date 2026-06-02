import type { LlmAvailabilityHints, LlmModeOption } from "../api/client";
import {
  isCloudCredentialsEnabled,
  type StoredRuntimeCredentials,
} from "../utils/runtimeCredentialsStorage";

/** 浏览器已配置 Key，或服务器已配 Key 时，视为云端可用。 */
export function isEffectiveCloudAvailable(
  apiCloudAvailable: boolean,
  creds: StoredRuntimeCredentials,
  serverCloudConfigured = false,
): boolean {
  return apiCloudAvailable || isCloudCredentialsEnabled(creds) || serverCloudConfigured;
}

/** 当前 UI 状态下是否需要本地 Ollama（由 API 字段推导，不写死 mode id）。 */
export function needsLocalRuntime(opt: LlmModeOption, compressEnabled: boolean): boolean {
  if (!opt.requires_local) return false;
  if (opt.compress_toggle) return compressEnabled;
  return true;
}

/** 当前 UI 状态下模式是否满足运行前置（不含本地模型名是否已填）。 */
export function isLlmModeRuntimeAvailable(
  opt: LlmModeOption,
  cloudAvailable: boolean,
  localAvailable: boolean,
  compressEnabled: boolean,
): boolean {
  if (opt.requires_cloud && !cloudAvailable) return false;
  if (needsLocalRuntime(opt, compressEnabled) && !localAvailable) return false;
  return true;
}

/** 根据 API 下发的 hints 推导不可提交原因（不写死中文文案）。 */
export function resolveUnavailableHint(
  opt: LlmModeOption,
  hints: LlmAvailabilityHints | null,
  cloudAvailable: boolean,
  localAvailable: boolean,
  compressEnabled: boolean,
  localModel: string,
): string | null {
  if (isLlmModeRuntimeAvailable(opt, cloudAvailable, localAvailable, compressEnabled)) {
    if (needsLocalRuntime(opt, compressEnabled) && localAvailable && !localModel.trim()) {
      if (opt.compress_toggle) return hints?.compress_model_required ?? null;
      return hints?.local_model_required ?? null;
    }
    return null;
  }
  if (hints) {
    if (opt.requires_cloud && !cloudAvailable) return hints.cloud_unavailable;
    if (needsLocalRuntime(opt, compressEnabled) && !localAvailable) {
      return opt.compress_toggle && compressEnabled
        ? hints.local_for_compress
        : hints.local_unavailable;
    }
  }
  return opt.unavailable_hint ?? null;
}
