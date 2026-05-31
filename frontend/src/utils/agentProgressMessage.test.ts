import { describe, expect, it } from "vitest";

import { resolveRunningMessage } from "./agentProgressMessage";
import type { AgentProgress } from "../api/client";

describe("resolveRunningMessage", () => {
  it("uses parallel_running_hint when two agents in same group are running", () => {
    const progress: AgentProgress[] = [
      {
        agent_id: 1,
        name: "A",
        status: "running",
        message: "",
        parallel_group: "scan",
      },
      {
        agent_id: 2,
        name: "B",
        status: "running",
        message: "single",
        parallel_group: "scan",
      },
    ];
    const msg = resolveRunningMessage(
      progress,
      { parallel_running_hint: "Parallel hint" },
      "fallback",
    );
    expect(msg).toBe("Parallel hint");
  });

  it("uses first running agent message when not parallel", () => {
    const progress: AgentProgress[] = [
      {
        agent_id: 3,
        name: "Diff",
        status: "running",
        message: "diff msg",
        parallel_group: null,
      },
    ];
    const msg = resolveRunningMessage(progress, {}, "fallback");
    expect(msg).toBe("diff msg");
  });
});
