import { cleanup, render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DetailPage from "./DetailPage";
import {
  mockDetailLlmOptions,
  mockDiagramMeta,
  mockRulesMeta,
} from "../test/fixtures/metaFixtures";

vi.mock("../api/client", () => ({
  exportUrl: (taskId: string) => `/api/tasks/${taskId}/export.md`,
  fetchClientMeta: vi.fn(),
  fetchDetailPageMeta: vi.fn(),
  fetchDiagramMeta: vi.fn(),
  fetchRulesMeta: vi.fn(),
  fetchLlmModeOptions: vi.fn(),
  getTask: vi.fn(),
  getTaskResult: vi.fn(),
  rerunTask: vi.fn(),
}));

import {
  fetchClientMeta,
  fetchDetailPageMeta,
  fetchDiagramMeta,
  fetchLlmModeOptions,
  fetchRulesMeta,
  getTask,
  getTaskResult,
} from "../api/client";
import { mockClientMeta, mockDetailPageMeta } from "../test/fixtures/metaFixtures";

const defaultTask = {
  id: "t1",
  input_type: "pr_url" as const,
  input_value: "x",
  status: "completed" as const,
  current_agent: 5,
  agent_progress: [],
  rerun_used: false,
  review_depth_mode: "balanced",
  review_depth_label: "标准审阅",
  llm_mode: "cloud_only",
  llm_mode_label: "纯云端",
};

const defaultResult = {
  summary: "s",
  summary_bullets: [],
  diagrams: [],
  risks: [],
  missing_info: [],
  degradation_notes: ["degraded"],
  diff_atoms: [{ id: "a1", file_path: "x.py", change_type: "modified", symbol: "", summary: "x" }],
  detected_project_type: "python-api",
  detected_framework: "FastAPI",
  review_stats: {
    review_depth_mode: "balanced",
    review_depth_label: "标准审阅",
    total_atoms: 2,
    reviewed_atoms: 1,
    batches_run: 1,
    pro_calls: 2,
    flash_calls: 1,
  },
};

describe("DetailPage", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(fetchClientMeta).mockReset();
    vi.mocked(fetchDetailPageMeta).mockReset();
    vi.mocked(fetchDiagramMeta).mockReset();
    vi.mocked(fetchRulesMeta).mockReset();
    vi.mocked(fetchLlmModeOptions).mockReset();
    vi.mocked(getTask).mockReset();
    vi.mocked(getTaskResult).mockReset();
    vi.mocked(fetchClientMeta).mockResolvedValue(mockClientMeta);
    vi.mocked(fetchDetailPageMeta).mockResolvedValue(mockDetailPageMeta);
    vi.mocked(fetchDiagramMeta).mockResolvedValue(mockDiagramMeta);
    vi.mocked(fetchRulesMeta).mockResolvedValue(mockRulesMeta);
    vi.mocked(fetchLlmModeOptions).mockResolvedValue(mockDetailLlmOptions);
    vi.mocked(getTask).mockResolvedValue(defaultTask);
    vi.mocked(getTaskResult).mockResolvedValue(defaultResult);
  });

  it("降级且空风险时展示提示条", async () => {
    render(
      <MemoryRouter initialEntries={["/tasks/t1"]}>
        <Routes>
          <Route path="/tasks/:taskId" element={<DetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(mockRulesMeta.ui_strings.degradation_banner)).toBeInTheDocument();
    });
    expect(screen.getByText(mockRulesMeta.ui_strings.no_risks_but_atoms_banner)).toBeInTheDocument();
    expect(screen.getByText(/Pro ×2 · Flash ×1/)).toBeInTheDocument();
    expect(screen.getAllByText(/已扫描 1\/2 个差异点/).length).toBeGreaterThan(0);
  });

  it("无 llmOptions 时仍按 markdown_report 展示规则报告", async () => {
    vi.mocked(fetchLlmModeOptions).mockRejectedValue(new Error("offline"));
    vi.mocked(getTask).mockResolvedValue({
      id: "t-rules",
      input_type: "patch",
      input_value: "x",
      status: "completed",
      current_agent: 5,
      agent_progress: [],
      rerun_used: false,
      review_depth_mode: "balanced",
      review_depth_label: "标准审阅",
      llm_mode: "rules_only",
      llm_mode_label: "纯规则",
      visualization_mode: "markdown",
      rerun_supported: false,
    });
    vi.mocked(getTaskResult).mockResolvedValue({
      summary: "规则摘要",
      summary_bullets: [],
      diagrams: [],
      risks: [],
      missing_info: [],
      degradation_notes: [],
      diff_atoms: [],
      detected_project_type: "",
      detected_framework: "",
      markdown_report: "## 摘要\n\n规则模式报告",
    });

    render(
      <MemoryRouter initialEntries={["/tasks/t-rules"]}>
        <Routes>
          <Route path="/tasks/:taskId" element={<DetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("navigation", { name: "任务详情导航" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: mockRulesMeta.ui_strings.nav_rule_hits })).not.toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "任务详情导航" });
    fireEvent.click(within(nav).getByRole("button", { name: mockRulesMeta.ui_strings.nav_report }));
    expect(screen.getByText("规则模式报告")).toBeInTheDocument();
  });

  it("rules_only 合并规则报告与规则命中 Tab", async () => {
    vi.mocked(fetchLlmModeOptions).mockRejectedValue(new Error("offline"));
    vi.mocked(getTask).mockResolvedValue({
      id: "t-merge",
      input_type: "patch",
      input_value: "x",
      status: "completed",
      current_agent: 5,
      agent_progress: [],
      rerun_used: false,
      review_depth_mode: "balanced",
      review_depth_label: "标准审阅",
      llm_mode: "rules_only",
      llm_mode_label: "纯规则",
      visualization_mode: "markdown",
      rerun_supported: false,
    });
    vi.mocked(getTaskResult).mockResolvedValue({
      summary: "规则摘要",
      summary_bullets: [],
      diagrams: [],
      risks: [],
      missing_info: [],
      degradation_notes: [],
      diff_atoms: [],
      detected_project_type: "",
      detected_framework: "",
      markdown_report: "## 摘要\n\n合并报告",
      rule_hits: [
        {
          rule_id: "hardcoded-secret",
          severity: "HIGH",
          file_path: "app/config.py",
          evidence: "password = '123'",
          message: "禁止硬编码密钥",
        },
      ],
    });

    render(
      <MemoryRouter initialEntries={["/tasks/t-merge"]}>
        <Routes>
          <Route path="/tasks/:taskId" element={<DetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("navigation", { name: "任务详情导航" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: mockRulesMeta.ui_strings.nav_rule_hits })).not.toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "任务详情导航" });
    fireEvent.click(within(nav).getByRole("button", { name: mockRulesMeta.ui_strings.nav_report }));
    expect(screen.getByText("合并报告")).toBeInTheDocument();
    expect(screen.getByText("禁止硬编码密钥")).toBeInTheDocument();
  });
});
