import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import MermaidDiagram from "./MermaidDiagram";

vi.mock("mermaid", () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(),
  },
}));

const UI = {
  render_error_title: "图表渲染失败",
  render_error_hint: "展开查看原始 Mermaid",
  unnamed_node: "未命名节点",
  empty_structure: "暂无结构数据",
};

describe("MermaidDiagram", () => {
  it("渲染失败时展示错误和原始代码", async () => {
    const mermaid = await import("mermaid");
    vi.mocked(mermaid.default.render).mockRejectedValueOnce(new Error("parse failed"));

    render(<MermaidDiagram code={"flowchart TB\nA-->B"} id="x" uiStrings={UI} />);

    await waitFor(() => {
      expect(screen.getByText(/图表渲染失败/)).toBeInTheDocument();
    });
    expect(screen.getByText(/展开查看原始 Mermaid/)).toBeInTheDocument();
  });
});
