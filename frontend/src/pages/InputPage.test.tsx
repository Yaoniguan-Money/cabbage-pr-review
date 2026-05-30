import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import InputPage from "./InputPage";
import {
  mockAvailabilityHints,
  mockDepthOptionsResponse,
  mockInputPageMeta,
  mockLlmOptionsResponse,
} from "../test/fixtures/metaFixtures";

vi.mock("../api/client", () => ({
  fetchInputPageMeta: vi.fn(),
  fetchReviewDepthOptions: vi.fn(),
  fetchLlmModeOptions: vi.fn(),
  fetchExamples: vi.fn(() => Promise.resolve([])),
  fetchDemoPatches: vi.fn(() => Promise.resolve([])),
  fetchRulesCatalog: vi.fn(() => Promise.reject(new Error("skip"))),
  createTask: vi.fn(),
}));

import { createTask, fetchInputPageMeta, fetchLlmModeOptions, fetchReviewDepthOptions } from "../api/client";

describe("InputPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(fetchInputPageMeta).mockReset();
    vi.mocked(fetchReviewDepthOptions).mockReset();
    vi.mocked(fetchLlmModeOptions).mockReset();
    vi.mocked(fetchInputPageMeta).mockResolvedValue(mockInputPageMeta);
    vi.mocked(fetchReviewDepthOptions).mockResolvedValue(mockDepthOptionsResponse);
    vi.mocked(fetchLlmModeOptions).mockResolvedValue(mockLlmOptionsResponse);
  });

  it("从 API 渲染审阅深度与推理模式文案", async () => {
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );
    await waitFor(() => {
      expect(fetchInputPageMeta).toHaveBeenCalled();
      expect(fetchReviewDepthOptions).toHaveBeenCalled();
      expect(fetchLlmModeOptions).toHaveBeenCalled();
    });
    expect(screen.getByText("标准审阅")).toBeInTheDocument();
    expect(screen.getByText("纯云端")).toBeInTheDocument();
    expect(screen.getByText("cloud-summary")).toBeInTheDocument();
    expect(screen.getByText("cloud-bullet")).toBeInTheDocument();
  });

  it("创建任务时传递 review_depth_mode 与 llm_mode", async () => {
    vi.mocked(createTask).mockResolvedValue({
      id: "t1",
      input_type: "pr_url",
      input_value: "x",
      status: "pending",
      current_agent: 0,
      agent_progress: [],
      rerun_used: false,
      review_depth_mode: "balanced",
      llm_mode: "cloud_only",
    });
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );
    await waitFor(() => expect(screen.getByText("标准审阅")).toBeInTheDocument());
    expect(fetchReviewDepthOptions).toHaveBeenCalled();
    expect(fetchLlmModeOptions).toHaveBeenCalled();
  });

  describe("local 不可用", () => {
    beforeEach(() => {
      vi.mocked(fetchLlmModeOptions).mockResolvedValue({
        options: [
          {
            id: "cloud_only",
            label: "纯云端",
            summary: "cloud-summary",
            detail_bullets: [],
            requires_cloud: true,
            requires_local: false,
            requires_llm: true,
            quality_warning: false,
            visualization_mode: "diagrams" as const,
            rerun_supported: true,
            hide_token_stats: false,
            default: true,
            available: true,
          },
          {
            id: "hybrid",
            label: "混合",
            summary: "hybrid-summary",
            detail_bullets: [],
            requires_cloud: true,
            requires_local: true,
            requires_llm: true,
            quality_warning: false,
            visualization_mode: "diagrams" as const,
            rerun_supported: true,
            hide_token_stats: false,
            default: false,
            available: false,
            unavailable_hint: "compress-local-hint",
            compress_toggle: {
              default_enabled: true,
              label: "启用压缩",
              hint_off: "关闭压缩",
            },
          },
          {
            id: "rules_only",
            label: "纯规则",
            summary: "rules-summary",
            detail_bullets: [],
            requires_cloud: false,
            requires_local: false,
            requires_llm: false,
            quality_warning: true,
            visualization_mode: "markdown" as const,
            rerun_supported: false,
            hide_token_stats: true,
            default: false,
            available: true,
          },
        ],
        default_llm_mode: "cloud_only",
        default_local_compress_enabled: true,
        cloud_available: true,
        local_available: false,
        local_models: [],
        default_local_model: "",
        availability_hints: mockAvailabilityHints,
      });
    });

    it("仍可点选混合并展示 API 提示", async () => {
      render(
        <BrowserRouter>
          <InputPage />
        </BrowserRouter>,
      );
      await waitFor(() => expect(screen.getByRole("heading", { name: "混合" })).toBeInTheDocument());
      fireEvent.click(screen.getByRole("heading", { name: "混合" }));
      await waitFor(() => {
        expect(screen.getByText("compress-local-hint")).toBeInTheDocument();
      });
    });
  });
});
