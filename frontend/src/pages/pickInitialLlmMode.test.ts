import { describe, expect, it } from "vitest";
import type { LlmModeOption } from "../api/client";
import { pickInitialLlmMode } from "./pickInitialLlmMode";

const envAll = {
  cloudAvailable: true,
  localAvailable: true,
  defaultCompressEnabled: true,
};

const envNoCloud = {
  cloudAvailable: false,
  localAvailable: false,
  defaultCompressEnabled: true,
};

const base = (overrides: Partial<LlmModeOption>): LlmModeOption => ({
  id: "x",
  label: "x",
  summary: "",
  detail_bullets: [],
  requires_cloud: false,
  requires_local: false,
  requires_llm: true,
  quality_warning: false,
  visualization_mode: "diagrams",
  rerun_supported: true,
  hide_token_stats: false,
  default: false,
  available: true,
  ...overrides,
});

describe("pickInitialLlmMode", () => {
  it("default 且运行时可用时选中 default", () => {
    const options = [
      base({ id: "cloud_only", default: true, requires_cloud: true }),
      base({ id: "rules_only", requires_llm: false }),
    ];
    expect(pickInitialLlmMode(options, envAll)).toBe("cloud_only");
  });

  it("cloud 不可用时自动选中纯规则", () => {
    const options = [
      base({ id: "cloud_only", default: true, requires_cloud: true }),
      base({ id: "rules_only", requires_llm: false }),
    ];
    expect(pickInitialLlmMode(options, envNoCloud)).toBe("rules_only");
  });
});
