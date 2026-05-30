import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InputPage from "./InputPage";

const mockDepthOptions = {
  options: [
    {
      id: "conservative",
      label: "快速审阅",
      summary: "summary-fast",
      detail_bullets: ["bullet-fast"],
      estimated_time: "3-5",
      cost_tier: "low" as const,
      default: false,
    },
    {
      id: "balanced",
      label: "标准审阅",
      summary: "summary-balanced",
      detail_bullets: ["bullet-balanced"],
      estimated_time: "4-7",
      cost_tier: "medium" as const,
      default: true,
    },
  ],
  default_review_depth_mode: "balanced",
};

const mockLlmOptions = {
  options: [
    {
      id: "cloud_only",
      label: "纯云端",
      summary: "cloud-summary",
      detail_bullets: ["cloud-bullet"],
      requires_cloud: true,
      requires_local: false,
      quality_warning: false,
      default: true,
      available: true,
    },
    {
      id: "hybrid",
      label: "混合",
      summary: "hybrid-summary",
      detail_bullets: ["hybrid-bullet"],
      requires_cloud: true,
      requires_local: true,
      quality_warning: false,
      default: false,
      available: true,
      compress_toggle: {
        default_enabled: true,
        label: "启用本地输入压缩",
        hint_off: "关闭后本地不参与",
      },
    },
  ],
  default_llm_mode: "cloud_only",
  default_local_compress_enabled: true,
  cloud_available: true,
  local_available: true,
  local_models: ["test-model:7b"],
  default_local_model: "",
};

vi.mock("../api/client", () => ({
  fetchReviewDepthOptions: vi.fn(() => Promise.resolve(mockDepthOptions)),
  fetchLlmModeOptions: vi.fn(() => Promise.resolve(mockLlmOptions)),
  fetchExamples: vi.fn(() => Promise.resolve([])),
  createTask: vi.fn(),
}));

import { createTask, fetchLlmModeOptions, fetchReviewDepthOptions } from "../api/client";

describe("InputPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("从 API 渲染审阅深度与推理模式文案", async () => {
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>
    );
    await waitFor(() => {
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
      </BrowserRouter>
    );
    await waitFor(() => expect(screen.getByText("标准审阅")).toBeInTheDocument());
    expect(fetchReviewDepthOptions).toHaveBeenCalled();
    expect(fetchLlmModeOptions).toHaveBeenCalled();
  });
});
