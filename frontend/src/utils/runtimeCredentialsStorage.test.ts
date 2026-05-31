import { describe, expect, it, beforeEach } from "vitest";

import {
  clearRuntimeCredentials,
  isCloudCredentialsEnabled,
  isGithubCredentialsEnabled,
  loadRuntimeCredentials,
  prepareCredentialsForSave,
  saveRuntimeCredentials,
} from "./runtimeCredentialsStorage";

describe("runtimeCredentialsStorage", () => {
  beforeEach(() => {
    clearRuntimeCredentials();
  });

  it("保存时若已填 Key 则自动启用云端开关", () => {
    const prepared = prepareCredentialsForSave({
      enable_cloud: false,
      enable_github: false,
      cloud_api_base: "https://api.deepseek.com",
      cloud_api_key: "sk-test",
      cloud_flash_model: "deepseek-v4-flash",
      cloud_pro_model: "deepseek-v4-pro",
      github_token: "",
    });
    expect(prepared.enable_cloud).toBe(true);
    expect(isCloudCredentialsEnabled(prepared)).toBe(true);

    saveRuntimeCredentials(prepared);
    const loaded = loadRuntimeCredentials();
    expect(loaded.cloud_api_key).toBe("sk-test");
    expect(loaded.enable_cloud).toBe(true);
    expect(loaded.cloud_flash_model).toBe("deepseek-v4-flash");
  });

  it("保存时若已填 GitHub Token 则自动启用 GitHub 开关", () => {
    const prepared = prepareCredentialsForSave({
      enable_cloud: false,
      enable_github: false,
      cloud_api_base: "",
      cloud_api_key: "",
      cloud_flash_model: "",
      cloud_pro_model: "",
      github_token: "ghp_test_token",
    });
    expect(prepared.enable_github).toBe(true);
    expect(isGithubCredentialsEnabled(prepared)).toBe(true);
  });
});
