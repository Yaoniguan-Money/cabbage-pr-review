import { describe, expect, it } from "vitest";

import { parseContentDispositionFilename } from "./parseContentDispositionFilename";

describe("parseContentDispositionFilename", () => {
  it("解析 quoted filename", () => {
    expect(
      parseContentDispositionFilename('attachment; filename="pr-review-abc.md"'),
    ).toBe("pr-review-abc.md");
  });

  it("无 header 时返回 null", () => {
    expect(parseContentDispositionFilename(null)).toBeNull();
  });
});
