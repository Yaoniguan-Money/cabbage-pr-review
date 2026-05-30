# AI PR Review 助手

基于定稿 v2.0 的 MVP：结构化 PR 影响分析与审阅辅助工具。

## 功能

- 三种输入：GitHub PR URL、Patch/Diff、本地仓库路径
- LangGraph 编排 5 个 Agent（原版本扫描 → PR 扫描 → 差异对比 → 递进审阅 → 可视化）
- 结果页：摘要条、三张 Mermaid 图、风险列表、缺失信息
- 支持一次补上下文重跑、Markdown 导出
- 局部降级：单 Agent 失败不阻断整体

## 配置 DeepSeek API（生产/验收必填）

在项目根目录创建 `.env`（可参考 `.env.example`）：

```env
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_FLASH_MODEL=deepseek-chat
DEEPSEEK_PRO_MODEL=deepseek-reasoner
USE_MOCK_LLM=false
```

启动后访问 http://localhost:8000/health ，应看到 `llm_enabled: true`、`model_profile: v22_provider_via_env`。

未配置 Key 且 `USE_MOCK_LLM=false` 时，**纯云端**模式下 `POST /api/tasks` 返回 **503**。

**依赖**：本机与 Docker 镜像均需安装 **git**（PR URL / 本地仓库路径用于 `git show` 读取 base/head 文件）。

## 快速启动

### 本地开发

```bash
# 在项目根目录 pr/ 下已有 .env 时，从 backend 启动即可自动加载
cd backend
pip install -r requirements.txt
set PYTHONPATH=.
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- 前端：http://localhost:8080
- 后端 API：http://localhost:8000
- 健康检查：http://localhost:8000/health

## 测试

```bash
cd backend
set PYTHONPATH=.
pytest tests/ -v
```

测试通过 `tests/conftest.py` **Mock** `flash_json_sync` / `pro_json_sync`，不消耗 DeepSeek 额度、不依赖启发式规则。

## 文档依据

- 主执行：[AI_PR_Review_助手执行计划_定稿_v2.0.docx](./AI_PR_Review_助手执行计划_定稿_v2.0.docx)
- 补充：[AI_PR_Review_助手执行计划_定稿_v2.0.md](./AI_PR_Review_助手执行计划_定稿_v2.0.md)

冲突时以 v2.0 为准。

## 质量回归（v2.1）

需 Docker + DeepSeek Key，详见 [docs/V2.1_QUALITY.md](./docs/V2.1_QUALITY.md)。

```powershell
.\scripts\quality_regression.ps1 -PrUrl "https://github.com/owner/repo/pull/N" -MinRisks 1 -MaxDegradationNotes 0
```

CI（GitHub Actions）仅跑 mock LLM 单元测试，不消耗 API 额度。

## 审阅深度（PR #4）

首页可选 **快速 / 标准 / 深度** 三档（文案由 `GET /api/review-depth-options` 下发）。环境变量 `REVIEW_DEPTH_MODE` 为服务端默认档。详见 [docs/V2.1_QUALITY.md](./docs/V2.1_QUALITY.md)。

## 推理模式（v2.2）

首页可选 **纯云端 / 混合 / 纯本地**（文案由 `GET /api/llm-mode-options` 下发）。混合模式默认 **开启本地输入压缩**；审阅结论仍由云端 Flash/Pro 生成。详见 [docs/V2.2_LLM_PROVIDER.md](./docs/V2.2_LLM_PROVIDER.md) 与 [docs/LOCAL_LLM_SETUP.md](./docs/LOCAL_LLM_SETUP.md)。

## Token 统计（v2.2+）

每个任务完成后，`GET /api/tasks/{id}` 返回 `token_stats`（云端/本地 prompt·completion·合计及 `display_segments` 展示文案）。Markdown 导出含 Token 小节。详见 [docs/TOKEN_STATS.md](./docs/TOKEN_STATS.md)。

## 图表可视化（v2.3）

三图差异化渲染、title/caption/图例、节点 risk/confidence 展示；文案与样式由 `GET /api/diagram-meta` 单源下发。详见 [docs/V2.3_DIAGRAMS.md](./docs/V2.3_DIAGRAMS.md)。

## 纯规则模式（v2.4）

首页可选 **纯规则** 第四档（`rules_only`）：零 LLM，YAML 规则引擎 + Markdown 报告；无需 Cloud/Ollama。详见 [docs/V2.4_RULES_MODE.md](./docs/V2.4_RULES_MODE.md)。

## 评委三步体验（推荐）

面向零配置演示：**真实规则引擎**为主路径，无需 API Key / Ollama。

1. `docker compose -f docker-compose.demo.yml up --build` → 打开 http://localhost:8080
2. 首页点击 **S1 / S2 / S3** 演示 Patch 一键加载 → 确认推理模式为 **纯规则**
3. **开始分析** → 查看 **规则报告** 页签（含 Markdown 报告与结构化规则命中），对照 [docs/JUDGE_DEMO.md](./docs/JUDGE_DEMO.md) 中的 `rule_id`

启动后可用 `GET /health` 验收规则包是否就绪（demo  compose 默认 `LLM_MODE=rules_only`）：

```bash
curl http://localhost:8000/health
```

| 字段 | 期望（demo / 纯规则） | 说明 |
|------|----------------------|------|
| `llm_mode` | `rules_only` | 当前推理模式 |
| `use_mock_llm` | `false` | demo 主路径不走 Mock LLM |
| `rules_pack_loaded` | `true` | 默认规则包已成功加载 |
| `rules_count` | `> 0`（当前约 16） | 有效规则条数 |
| `rules_invalid_count` | `0` | YAML lint 失败条数；非 0 表示规则包需修复 |

`rules_invalid_count > 0` 时任务仍可运行，但应优先修复 `backend/app/rules/packs/default/` 下对应 YAML，再跑 `pytest backend/tests/test_rules_lint.py`。

可选：[`docker-compose.demo-mock.yml`](./docker-compose.demo-mock.yml) 展示 Mock LLM 四图 UI（附录，见 JUDGE_DEMO）。

### 开源借鉴与许可证

| 来源 | 许可证 | 本项目用法 |
|------|--------|------------|
| [Semgrep](https://github.com/semgrep/semgrep) | LGPL-2.1 | **仅借鉴** YAML 规则字段设计，未引入引擎或 semgrep-rules 规则包 |
| [reviewdog](https://github.com/reviewdog/reviewdog) | MIT | **仅借鉴** diff 范围运行与 severity 分级思路 |
| [Danger](https://github.com/danger/danger) | MIT | **仅借鉴** PR 上下文变量与 fail/warn 分级映射 |

默认规则包位于 `backend/app/rules/packs/default/`（随 Docker `COPY app` 一并打包）。
