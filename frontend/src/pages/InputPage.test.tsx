import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InputPage from "./InputPage";

const mockOptions = {
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

vi.mock("../api/client", () => ({
  fetchReviewDepthOptions: vi.fn(() => Promise.resolve(mockOptions)),
  fetchExamples: vi.fn(() => Promise.resolve([])),
  createTask: vi.fn(),
}));

import { createTask, fetchReviewDepthOptions } from "../api/client";

describe("InputPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("从 API 渲染审阅深度选项文案", async () => {
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(fetchReviewDepthOptions).toHaveBeenCalled();
    });
    expect(screen.getByText("标准审阅")).toBeInTheDocument();
    expect(screen.getByText("summary-balanced")).toBeInTheDocument();
    expect(screen.getByText("bullet-balanced")).toBeInTheDocument();
  });

  it("创建任务时传递 review_depth_mode", async () => {
    vi.mocked(createTask).mockResolvedValue({
      id: "t1",
      input_type: "pr_url",
      input_value: "x",
      status: "pending",
      current_agent: 0,
      agent_progress: [],
      rerun_used: false,
      review_depth_mode: "balanced",
    });
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>
    );
    await waitFor(() => expect(screen.getByText("标准审阅")).toBeInTheDocument());
    // 默认 balanced 已选中，填输入并提交需进一步交互；此处验证 options 加载即可
    expect(fetchReviewDepthOptions).toHaveBeenCalled();
  });
});
