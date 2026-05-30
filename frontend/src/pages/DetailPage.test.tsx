import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import DetailPage from "./DetailPage";

vi.mock("../api/client", () => ({
  exportUrl: (taskId: string) => `/api/tasks/${taskId}/export.md`,
  fetchDiagramMeta: vi.fn(async () => ({
    section_label: "三张图",
    section_preview_label: "三张图（预览）",
    empty_diagrams: "暂无图表",
    ui_strings: {
      render_error_title: "图表渲染失败",
      render_error_hint: "展开查看原始 Mermaid",
      unnamed_node: "未命名节点",
      empty_structure: "暂无结构数据",
    },
    default_legend: [],
    diagram_types: [],
  })),
  getTask: vi.fn(async () => ({
    id: "t1",
    input_type: "pr_url",
    input_value: "x",
    status: "completed",
    current_agent: 5,
    agent_progress: [],
    rerun_used: false,
    review_depth_mode: "balanced",
    review_depth_label: "标准审阅",
  })),
  getTaskResult: vi.fn(async () => ({
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
  })),
  rerunTask: vi.fn(),
}));

describe("DetailPage", () => {
  it("降级且空风险时展示提示条", async () => {
    render(
      <MemoryRouter initialEntries={["/tasks/t1"]}>
        <Routes>
          <Route path="/tasks/:taskId" element={<DetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/本次分析包含降级项/)).toBeInTheDocument();
    });
    expect(screen.getByText(/当前未提取到风险项/)).toBeInTheDocument();
    expect(screen.getByText(/已扫描 1\/2 个差异点/)).toBeInTheDocument();
    expect(screen.getByText(/Pro ×2 · Flash ×1/)).toBeInTheDocument();
  });
});
