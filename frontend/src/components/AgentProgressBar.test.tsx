import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AgentProgressBar from "./AgentProgressBar";
import type { AgentProgress } from "../api/client";

const baseProgress: AgentProgress[] = [
  {
    agent_id: 1,
    name: "Base Scan",
    status: "running",
    message: "",
    parallel_group: "scan",
  },
  {
    agent_id: 2,
    name: "PR Scan",
    status: "running",
    message: "",
    parallel_group: "scan",
  },
  {
    agent_id: 3,
    name: "Diff",
    status: "pending",
    message: "",
    parallel_group: null,
  },
];

describe("AgentProgressBar", () => {
  it("shows parallel-active lane when two steps in same group are running", () => {
    const { container } = render(
      <AgentProgressBar
        progress={baseProgress}
        stepperLabel="Progress"
        parallelLaneAria="Parallel scan lane"
      />,
    );
    const lane = container.querySelector(".agent-stepper-parallel-lane.parallel-active");
    expect(lane).toBeTruthy();
    expect(screen.getByText("Base Scan")).toBeTruthy();
    expect(screen.getByText("PR Scan")).toBeTruthy();
  });

  it("does not mark parallel-active when only one scan step is running", () => {
    const progress: AgentProgress[] = [
      { ...baseProgress[0], status: "running" },
      { ...baseProgress[1], status: "pending" },
    ];
    const { container } = render(<AgentProgressBar progress={progress} />);
    expect(container.querySelector(".parallel-active")).toBeNull();
  });
});
