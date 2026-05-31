import { describe, expect, it } from "vitest";

import type { TaskRecord, TaskResult } from "../api/client";
import { buildPatchFiles } from "./buildPatchFiles";

describe("buildPatchFiles", () => {
  it("优先使用 pr_context.patches", () => {
    const task: TaskRecord = {
      id: "t1",
      input_type: "pr_url",
      input_value: "https://github.com/o/r/pull/1",
      status: "running",
      current_agent: 1,
      agent_progress: [],
      rerun_used: false,
      pr_context: {
        patches: [
          {
            filename: "src/a.ts",
            status: "modified",
            patch: "@@ -1 +1 @@\n-old\n+new",
            additions: 1,
            deletions: 1,
          },
        ],
      },
    };
    const files = buildPatchFiles(task, null);
    expect(files).toHaveLength(1);
    expect(files[0].filename).toBe("src/a.ts");
    expect(files[0].patch).toContain("+new");
  });

  it("patches 无 additions/deletions 时从 patch 文本统计", () => {
    const task: TaskRecord = {
      id: "t2",
      input_type: "pr_url",
      input_value: "demo",
      status: "completed",
      current_agent: 5,
      agent_progress: [],
      rerun_used: false,
      pr_context: {
        patches: [
          {
            filename: "Dockerfile",
            status: "modified",
            patch: "@@ -1,2 +1,3 @@\n-old\n+new\n+also",
          },
        ],
      },
    };
    const files = buildPatchFiles(task, null);
    expect(files[0].additions).toBe(2);
    expect(files[0].deletions).toBe(1);
  });

  it("无 patches 时回退 diff_atoms.hunk_patch", () => {
    const result: TaskResult = {
      summary: "",
      summary_bullets: [],
      diagrams: [],
      risks: [],
      missing_info: [],
      degradation_notes: [],
      diff_atoms: [
        {
          id: "a1",
          file_path: "b.py",
          change_type: "modified",
          symbol: "",
          summary: "",
          hunk_patch: "@@ -2 +2 @@\n-x",
        },
      ],
      detected_project_type: "",
      detected_framework: "",
    };
    const files = buildPatchFiles(null, result);
    expect(files[0].filename).toBe("b.py");
    expect(files[0].patch).toContain("-x");
  });
});
