import type { LlmModeOption } from "../api/client";
import { isLlmModeRuntimeAvailable } from "./llmModeAvailability";

export type LlmModePickEnv = {
  cloudAvailable: boolean;
  localAvailable: boolean;
  defaultCompressEnabled: boolean;
};

/** 优先 default 且运行时可用；否则选第一个可用档。 */
export function pickInitialLlmMode(options: LlmModeOption[], env: LlmModePickEnv): string {
  const isAvailable = (o: LlmModeOption) =>
    isLlmModeRuntimeAvailable(o, env.cloudAvailable, env.localAvailable, env.defaultCompressEnabled);

  const preferred = options.find((o) => o.default && isAvailable(o));
  if (preferred) return preferred.id;
  const firstAvailable = options.find(isAvailable);
  return firstAvailable?.id ?? options[0]?.id ?? "";
}
