import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import InputPage from "./InputPage";
import {
  mockAvailabilityHints,
  mockDepthOptionsResponse,
  mockClientMeta,
  mockInputPageMeta,
  mockLlmOptionsResponse,
} from "../test/fixtures/metaFixtures";
import { clearRuntimeCredentials } from "../utils/runtimeCredentialsStorage";

const mockLlmOptionsPublicNoCloud = {
  options: [
    {
      id: "cloud_only",
      label: "纯云端",
      summary: "cloud-summary",
      detail_bullets: ["cloud-bullet"],
      requires_cloud: true,
      requires_local: false,
      requires_llm: true,
      quality_warning: false,
      visualization_mode: "diagrams" as const,
      rerun_supported: true,
      hide_token_stats: false,
      default: true,
      available: false,
    },
    {
      id: "rules_only",
      label: "纯规则",
      summary: "rules-summary",
      detail_bullets: ["rules-bullet"],
      requires_cloud: false,
      requires_local: false,
      requires_llm: false,
      quality_warning: true,
      visualization_mode: "markdown" as const,
      rerun_supported: false,
      hide_token_stats: true,
      default: false,
      available: true,
    },
  ],
  default_llm_mode: "rules_only",
  default_local_compress_enabled: true,
  cloud_available: false,
  local_available: false,
  local_models: [],
  default_local_model: "",
  availability_hints: mockAvailabilityHints,
};

const mockRuntimeConfigMeta = {
  allow_runtime_credentials: true,
  deploy_mode: "local",
  is_public_deploy: false,
  server_cloud_configured: false,
  server_github_configured: false,
  expand_panel_default: false,
  ui_strings: {
    panel_title: "API 设置",
    panel_summary: "",
    onboarding_banner: "如想体验最佳效果请配置您的 API Key",
    preset_label: "预设",
    api_base_label: "Base",
    api_key_label: "Key",
    flash_model_label: "Flash",
    pro_model_label: "Pro",
    github_token_label: "GitHub",
    save_local_button: "保存",
    clear_button: "清除",
    saved_hint: "已保存",
    toggle_cloud_label: "启用云端 LLM API",
    toggle_github_label: "启用 GitHub Token",
    status_cloud_ready: "云端就绪",
    status_cloud_off: "云端未就绪",
    status_cloud_server: "服务器云端",
    status_github_ready: "GitHub 就绪",
    status_github_off: "GitHub 未就绪",
    status_github_server: "服务器 GitHub",
    status_local_ready: "本地就绪",
    status_local_off: "本地未就绪",
    status_cloud_public: "云端公网提示",
    status_github_public: "GitHub 公网提示",
  },
};

const mockRuntimePreview = {
  cloud_available: false,
  github_token_configured: false,
  local_available: false,
  server_cloud_configured: false,
  server_github_configured: false,
};

vi.mock("../api/client", () => ({
  fetchInputPageMeta: vi.fn(),
  fetchReviewDepthOptions: vi.fn(),
  fetchLlmModeOptions: vi.fn(),
  fetchClientMeta: vi.fn(() => Promise.resolve({ error_messages: {}, cloud_unavailable_banner: "" })),
  fetchRuntimeConfigMeta: vi.fn(() => Promise.resolve(mockRuntimeConfigMeta)),
  fetchRuntimeConfigPreview: vi.fn(() => Promise.resolve(mockRuntimePreview)),
  fetchProviderPresets: vi.fn(() =>
    Promise.resolve({
      presets: [
        {
          id: "deepseek",
          label: "DeepSeek",
          api_base: "https://api.deepseek.com",
          flash_model: "deepseek-chat",
          pro_model: "deepseek-reasoner",
        },
      ],
    }),
  ),
  fetchExamples: vi.fn(() => Promise.resolve([])),
  fetchDemoPatches: vi.fn(() => Promise.resolve([])),
  fetchRulesCatalog: vi.fn(() => Promise.reject(new Error("skip"))),
  createTask: vi.fn(),
}));

import { createTask, fetchInputPageMeta, fetchLlmModeOptions, fetchReviewDepthOptions } from "../api/client";

describe("InputPage", () => {
  afterEach(() => {
    cleanup();
    clearRuntimeCredentials();
  });

  beforeEach(() => {
    clearRuntimeCredentials();
    vi.mocked(fetchInputPageMeta).mockReset();
    vi.mocked(fetchReviewDepthOptions).mockReset();
    vi.mocked(fetchLlmModeOptions).mockReset();
    vi.mocked(fetchInputPageMeta).mockResolvedValue(mockInputPageMeta);
    vi.mocked(fetchReviewDepthOptions).mockResolvedValue(mockDepthOptionsResponse);
    vi.mocked(fetchLlmModeOptions).mockResolvedValue(mockLlmOptionsResponse);
  });

  it("展示首页使用说明与凭据开关", async () => {
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText("使用说明")).toBeInTheDocument();
      expect(screen.getByText(/不会在服务器上保存/)).toBeInTheDocument();
      expect(screen.getByText("启用云端 LLM API")).toBeInTheDocument();
    });
  });

  it("展示首页温馨提示", async () => {
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText("温馨提示")).toBeInTheDocument();
      expect(screen.getByText(/若希望发挥全部性能/)).toBeInTheDocument();
      expect(screen.getByText("启用云端 LLM API")).toBeInTheDocument();
      expect(screen.getByText("启用 GitHub Token")).toBeInTheDocument();
    });
  });

  it("从 API 渲染审阅深度与推理模式文案", async () => {
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );
    await waitFor(() => {
      expect(fetchInputPageMeta).toHaveBeenCalled();
      expect(fetchReviewDepthOptions).toHaveBeenCalled();
      expect(fetchLlmModeOptions).toHaveBeenCalled();
    });
    expect(screen.getByText("标准审阅")).toBeInTheDocument();
    expect(screen.getByText("纯云端")).toBeInTheDocument();
    expect(screen.getByText("cloud-summary")).toBeInTheDocument();
    expect(screen.getByText("cloud-bullet")).toBeInTheDocument();
  });

  it("云端不可用时展示 client-meta 横幅", async () => {
    const { fetchClientMeta } = await import("../api/client");
    vi.mocked(fetchClientMeta).mockResolvedValue({
      ...mockClientMeta,
      cloud_unavailable_banner: "如想体验最佳效果请配置您的 API Key",
    });
    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("如想体验最佳效果请配置您的 API Key");
    });
  });

  it("保存凭据后纯云端可点选且隐藏云端不可用横幅", async () => {
    const { fetchClientMeta, fetchRuntimeConfigPreview } = await import("../api/client");
    vi.mocked(fetchClientMeta).mockResolvedValue({
      ...mockClientMeta,
      cloud_unavailable_banner: "如想体验最佳效果请配置您的 API Key",
    });
    vi.mocked(fetchLlmModeOptions).mockImplementation((hasRuntimeCloudKey = false) =>
      Promise.resolve(hasRuntimeCloudKey ? mockLlmOptionsResponse : mockLlmOptionsPublicNoCloud),
    );
    vi.mocked(fetchRuntimeConfigPreview).mockImplementation(async (payload) => ({
      cloud_available: Boolean(payload?.cloud_api_key?.trim()),
      github_token_configured: false,
      local_available: false,
      server_cloud_configured: false,
      server_github_configured: false,
    }));

    render(
      <BrowserRouter>
        <InputPage />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("如想体验最佳效果请配置您的 API Key");
    });

    fireEvent.click(screen.getByRole("button", { name: "API 设置" }));
    fireEvent.click(screen.getByLabelText("启用云端 LLM API"));
    fireEvent.change(screen.getByLabelText("Key"), { target: { value: "sk-test-key" } });
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => {
      expect(fetchLlmModeOptions).toHaveBeenCalledWith(true);
    });

    await waitFor(() => {
      expect(screen.queryByText("如想体验最佳效果请配置您的 API Key")).not.toBeInTheDocument();
      expect(screen.queryByText("cloud-off-hint")).not.toBeInTheDocument();
    });

    const cloudHeading = screen.getByRole("heading", { name: "纯云端" });
    const cloudCard = cloudHeading.closest(".option-item");
    expect(cloudCard).not.toHaveClass("disabled");

    fireEvent.click(cloudHeading);
    await waitFor(() => {
      expect(cloudCard).toHaveClass("active");
    });
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
      </BrowserRouter>,
    );
    await waitFor(() => expect(screen.getByText("标准审阅")).toBeInTheDocument());
    expect(fetchReviewDepthOptions).toHaveBeenCalled();
    expect(fetchLlmModeOptions).toHaveBeenCalled();
  });

  describe("local 不可用", () => {
    beforeEach(() => {
      vi.mocked(fetchLlmModeOptions).mockResolvedValue({
        options: [
          {
            id: "cloud_only",
            label: "纯云端",
            summary: "cloud-summary",
            detail_bullets: [],
            requires_cloud: true,
            requires_local: false,
            requires_llm: true,
            quality_warning: false,
            visualization_mode: "diagrams" as const,
            rerun_supported: true,
            hide_token_stats: false,
            default: true,
            available: true,
          },
          {
            id: "hybrid",
            label: "混合",
            summary: "hybrid-summary",
            detail_bullets: [],
            requires_cloud: true,
            requires_local: true,
            requires_llm: true,
            quality_warning: false,
            visualization_mode: "diagrams" as const,
            rerun_supported: true,
            hide_token_stats: false,
            default: false,
            available: false,
            unavailable_hint: "compress-local-hint",
            compress_toggle: {
              default_enabled: true,
              label: "启用压缩",
              hint_off: "关闭压缩",
            },
          },
          {
            id: "rules_only",
            label: "纯规则",
            summary: "rules-summary",
            detail_bullets: [],
            requires_cloud: false,
            requires_local: false,
            requires_llm: false,
            quality_warning: true,
            visualization_mode: "markdown" as const,
            rerun_supported: false,
            hide_token_stats: true,
            default: false,
            available: true,
          },
        ],
        default_llm_mode: "cloud_only",
        default_local_compress_enabled: true,
        cloud_available: true,
        local_available: false,
        local_models: [],
        default_local_model: "",
        availability_hints: mockAvailabilityHints,
      });
    });

    it("local 不可用时混合模式卡片为 disabled", async () => {
      render(
        <BrowserRouter>
          <InputPage />
        </BrowserRouter>,
      );
      await waitFor(() => expect(screen.getByRole("heading", { name: "混合" })).toBeInTheDocument());
      const hybridCard = screen.getByRole("heading", { name: "混合" }).closest(".option-item");
      expect(hybridCard).toHaveClass("disabled");
    });
  });
});
