# AI PR Review 助手



基于定稿 v2.0 的 MVP：结构化 PR 影响分析与审阅辅助工具。



## 公网部署（评委自备 API Key）

服务器**不托管**你的个人 Key。部署见 [docs/CLOUD_DEPLOY.md](./docs/CLOUD_DEPLOY.md)。

评委打开站点后，首页提示：**如想体验最佳效果请配置您的 API Key** → 在「API 与 GitHub 设置」中填写 → 选择 **纯云端** 开始分析。

## 最快体验（零 API Key，推荐首次 clone）



**前提**：本机已安装并启动 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（或等价引擎），端口 8000 / 8080 未被占用。



无需复制 `.env`、无需 DeepSeek / GitHub Token。仓库已提交 [`.env.demo`](.env.demo)，`docker compose` 会自动加载；若你另有 `.env` 则会覆盖 demo 默认值。



```bash

git clone <repo> && cd <repo>

docker compose up --build

```



Windows 也可一键：



```powershell

.\scripts\start-demo.ps1

```



或（已安装 Make 时）：`make demo`



1. 打开 http://localhost:8080

2. 首页 **评委演示 Patch** 区域点击 **S1 / S2 / S3** → 确认推理模式为 **纯规则**

3. **开始分析** → 查看规则报告与命中，对照 [docs/JUDGE_DEMO.md](./docs/JUDGE_DEMO.md)



验收：`curl http://localhost:8000/health` 应见 `llm_mode=rules_only`、`rules_pack_loaded=true`、`rules_invalid_count=0`。



旧文档中的 `docker compose -f docker-compose.demo.yml up` 与上述命令**等价**（见 [`docker-compose.demo.yml`](./docker-compose.demo.yml)）。



---



## 功能



- 两种界面输入：GitHub PR URL、Patch/Diff（`local_path` API 仍保留，供本机/集成直调，输入页未暴露）

- LangGraph 编排 5 个 Agent（原版本扫描 → PR 扫描 → 差异对比 → 递进审阅 → 可视化）

- 结果页：摘要条、三张 Mermaid 图、风险列表、缺失信息

- 支持一次补上下文重跑、Markdown 导出

- 局部降级：单 Agent 失败不阻断整体

- **纯规则模式**（`rules_only`）：零 LLM，YAML 规则引擎，适合零密钥演示与 CI



## 生产 / 完整云端审阅（需 DeepSeek API Key）



复制环境文件并填入密钥（会覆盖 `.env.demo` 中的 `LLM_MODE=rules_only`）：



```bash

cp .env.example .env

# 编辑 .env：DEEPSEEK_API_KEY、可选 GITHUB_TOKEN、LLM_MODE=cloud_only

docker compose up --build

```



或：`make prod`（若不存在 `.env` 会从 `.env.example` 复制一份，仍需手动填 Key）



```env

DEEPSEEK_API_KEY=你的密钥

DEEPSEEK_BASE_URL=https://api.deepseek.com

DEEPSEEK_FLASH_MODEL=deepseek-chat

DEEPSEEK_PRO_MODEL=deepseek-reasoner

USE_MOCK_LLM=false

LLM_MODE=cloud_only

```



启动后访问 http://localhost:8000/health ，应看到 `llm_enabled: true`、`cloud_available: true`。



未配置 Key 且 `USE_MOCK_LLM=false` 时，若手动选择 **纯云端** 并提交任务，`POST /api/tasks` 返回 **503**（无 Key 时前端会自动优先 **纯规则**，见首页提示横幅）。



**依赖**：本机与 Docker 镜像均需安装 **git**（PR URL 分析时用于 `git show` 读取 base/head 文件）。分析 GitHub PR 建议配置 `GITHUB_TOKEN`，否则易遇 API 限流（403）。



## 本地开发



**环境**：Python **3.12**、Node **20**、**git**（PR URL 路径必装；`git --version` 自检）。



```bash

# 后端（在项目根或 backend 下；根目录 .env 可选，无 Key 时可用纯规则 + Patch）

cd backend

pip install -r requirements.txt

# Windows PowerShell / CMD：

set PYTHONPATH=.

# Linux / macOS：

# export PYTHONPATH=.



uvicorn app.main:app --reload --port 8000



# 前端（新终端）

cd frontend

npm install

npm run dev

```



浏览器打开 http://localhost:5173（Vite 将 `/api`、`/health` 代理到 8000）。



无 `.env` 时后端默认 `LLM_MODE=cloud_only`，但云端不可用时会由前端自动选用 **纯规则**；也可复制 `.env.demo` 为 `.env` 固定演示配置。



## 测试



```bash

cd backend

# Windows:

set PYTHONPATH=.

# Linux / macOS: export PYTHONPATH=.

pytest tests/ -v

```



测试通过 `tests/conftest.py` **Mock** LLM，不消耗 DeepSeek 额度。



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



首页可选 **纯云端 / 混合 / 纯本地 / 纯规则**（文案由 `GET /api/llm-mode-options` 下发）。详见 [docs/V2.2_LLM_PROVIDER.md](./docs/V2.2_LLM_PROVIDER.md) 与 [docs/LOCAL_LLM_SETUP.md](./docs/LOCAL_LLM_SETUP.md)。



## Token 统计（v2.2+）



详见 [docs/TOKEN_STATS.md](./docs/TOKEN_STATS.md)。



## 图表可视化（v2.3）



详见 [docs/V2.3_DIAGRAMS.md](./docs/V2.3_DIAGRAMS.md)。



## 纯规则模式（v2.4）



详见 [docs/V2.4_RULES_MODE.md](./docs/V2.4_RULES_MODE.md)。评委演示步骤详见 [docs/JUDGE_DEMO.md](./docs/JUDGE_DEMO.md)。



可选附录：[`docker-compose.demo-mock.yml`](./docker-compose.demo-mock.yml) 展示 Mock LLM 四图 UI（非规则主叙事）。



### 开源借鉴与许可证



| 来源 | 许可证 | 本项目用法 |

|------|--------|------------|

| [Semgrep](https://github.com/semgrep/semgrep) | LGPL-2.1 | **仅借鉴** YAML 规则字段设计 |

| [reviewdog](https://github.com/reviewdog/reviewdog) | MIT | **仅借鉴** diff 范围运行与 severity 分级 |

| [Danger](https://github.com/danger/danger) | MIT | **仅借鉴** PR 上下文变量与 fail/warn 分级 |



默认规则包位于 `backend/app/rules/packs/default/`。

