# AI PR Review 助手

结构化 PR 影响分析与审阅辅助工具：LangGraph 编排五个 Agent（原版本扫描 → PR 扫描 → 差异对比 → 递进审阅 → 可视化），并支持 **多种推理模式**，以同一套审阅工作流服务不同场景与用户群体。

### 为何提供多种推理模式

我们刻意保留 **纯云端、混合、纯本地、纯规则** 四档能力，并非简单堆功能，而是面向 **多受众、多采购场景** 的产品矩阵：

| 模式 | 典型受众 | 价值主张 |
|------|----------|----------|
| **纯云端** | 希望快速体验最新大模型能力的开发者 | 质量与能力迭代跟进行业主流 API |
| **混合** | 高频审阅、关注 Token 成本与响应效率的团队 | 审阅结论仍由云端生成，可选本地 Ollama 压缩长上下文，在体验新模型的同时控制成本 |
| **纯本地** | 有数据主权、合规与内网部署要求的企业用户 | 审阅链路可完全落在自有 Ollama 环境，代码与密钥不出公网，适合金融、政务及敏感代码库 |
| **纯规则** | 「不想折腾 API」的用户 | 零 Key、可审计、可复现，完整呈现规则命中、差异分析与报告结构，适合快速评估与流水线集成 |

公网演示站默认推荐 **纯规则 + S1/S2/S3 Patch**；若需完整 LLM 审阅，可在浏览器自备 Key 切换 **纯云端** 或 **混合**（详见下文「在线体验」）。

---

## 在线体验（评委 / 访客入口）

| | 链接 |
|---|------|
| **公网演示站点（推荐）** | **http://47.96.155.7:8080** |
| **健康检查（API）** | http://47.96.155.7:8000/health |
| **Demo 资料包（夸克网盘）** | **https://pan.quark.cn/s/dc36c81535ea** |

> 网盘分享名：**PR-review demo**。可用夸克 APP 或浏览器打开链接下载；内含演示说明与补充材料（若与线上一致，以公网站点为准）。

### 公网 3 分钟体验（无需 API Key）

1. 浏览器打开 **http://47.96.155.7:8080**（须为 `http`，端口 **8080**）。
2. 首页展开 **《使用说明》**（可选阅读）。
3. 在 **评委演示 Patch** 区域点击 **S1 / S2 / S3** → **加载场景**。
4. 推理模式保持 **纯规则**（`rules_only`，服务器未配置 Key）。
5. 点击 **开始分析**，在详情页查看规则报告、命中与图表；完整步骤见 [docs/JUDGE_DEMO.md](./docs/JUDGE_DEMO.md)。

### 可选：自备 Key 体验完整 LLM 审阅

- 在首页 **「API 与 GitHub 设置」** 中填写 **DeepSeek API Key**（仅存浏览器 localStorage，**不会**写入服务器）。
- 将推理模式改为 **纯云端** 后再提交任务。
- 分析 GitHub PR 链接时建议同时填写 **GitHub Token**，避免 API 限流。

### 服务说明

- 公网实例为 **演示环境**（`DEPLOY_MODE=public`），请勿在服务器配置个人密钥。
- 若页面无法打开，请确认使用 `http://` 且安全组已放行 **TCP 8080**；部署与排障见 [docs/ALIYUN_DEPLOY.md](./docs/ALIYUN_DEPLOY.md)。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12、FastAPI、Pydantic、LangGraph、httpx |
| 前端 | React 18、TypeScript、Vite 5、Mermaid、Vitest |
| 编排与部署 | Docker Compose、Caddy（公网 TLS）、GitHub Actions CI |
| 推理 | DeepSeek API（可选）、Ollama（混合压缩）、YAML 规则引擎（`rules_only`） |

## 仓库结构

```
backend/          # FastAPI 应用与 pytest 套件
frontend/         # React SPA 与 Vitest 套件
data/demo/        # 评委演示 S1/S2/S3 Patch 与合成仓库
docs/             # JUDGE_DEMO.md、CLOUD_DEPLOY.md
scripts/          # 演示启动、公网部署、质量回归（可选）
```

## 最快体验（零 API Key，推荐首次 clone）

**前提**：已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（或等价引擎），端口 8000 / 8080 未被占用。

```bash
git clone <repo> && cd <repo>
docker compose up --build
```

Windows 一键：`.\scripts\start-demo.ps1`  
已安装 Make：`make demo`

1. 打开 http://localhost:8080
2. 首页 **评委演示 Patch** 点击 **S1 / S2 / S3**，推理模式为 **纯规则**
3. **开始分析** → 对照 [docs/JUDGE_DEMO.md](./docs/JUDGE_DEMO.md)

验收：`curl http://localhost:8000/health` 应见 `llm_mode=rules_only`、`rules_pack_loaded=true`、`rules_invalid_count=0`。

仓库已提交 [`.env.demo`](.env.demo)；若本地另有 `.env` 会覆盖 demo 默认值。`docker compose -f docker-compose.demo.yml up` 与默认 `docker compose up` **等价**。

## 完整云端审阅（需 DeepSeek API Key）

```bash
cp .env.example .env
# 编辑：DEEPSEEK_API_KEY、可选 GITHUB_TOKEN、LLM_MODE=cloud_only
docker compose up --build
```

或 `make prod`（无 `.env` 时从 `.env.example` 复制，仍需手动填 Key）。

```env
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro
USE_MOCK_LLM=false
LLM_MODE=cloud_only
```

启动后 http://localhost:8000/health 应见 `llm_enabled: true`。未配置 Key 且选择 **纯云端** 时 `POST /api/tasks` 返回 **503**；前端会优先引导 **纯规则**。

**依赖**：本机与镜像均需 **git**（PR URL 分析用 `git show`）。分析 GitHub PR 建议配置 `GITHUB_TOKEN`，否则易 403 限流。

## 自行部署到公网

当前线上演示地址：**http://47.96.155.7:8080**（阿里云 ECS，方案 A：`docker compose` + 端口 8080）。

**阿里云 ECS**：见 [docs/ALIYUN_DEPLOY.md](./docs/ALIYUN_DEPLOY.md)。首次 `./scripts/aliyun-setup-demo.sh`；日常更新 `./scripts/aliyun-update.sh`（含国内 apt / pip / npm / Docker Hub 加速）。

**自有域名 + HTTPS**：见 [docs/CLOUD_DEPLOY.md](./docs/CLOUD_DEPLOY.md)，服务器**不托管**个人 Key。

- 复制 [`.env.production.example`](.env.production.example) 为 `.env.production`，`DEPLOY_MODE=public`，**勿填** `DEEPSEEK_API_KEY` / `GITHUB_TOKEN`
- 评委在浏览器「API 与 GitHub 设置」填写 Key（仅存 **localStorage**，不上传服务端日志）
- 不填 Key 仍可用 **纯规则** 与 S1/S2/S3 演示 Patch

## 本地开发

**环境**：Python **3.12**、Node **20**、**git**。

```bash
# 后端
cd backend
pip install -r requirements.txt
# Windows: set PYTHONPATH=.
# Linux/macOS: export PYTHONPATH=.
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

浏览器 http://localhost:5173（Vite 将 `/api`、`/health` 代理到 8000）。无 `.env` 时可复制 `.env.demo` 为 `.env` 固定演示配置。

## 推理模式与环境变量

首页选项由 `GET /api/llm-mode-options` 下发（前端不硬编码文案）。各模式与上表受众定位一致，可按部署环境组合使用：

| `LLM_MODE` | 说明 | 适用场景 |
|------------|------|----------|
| `rules_only` | 纯 YAML 规则引擎，零 LLM | 公网演示、评委验收、CI 门禁、零配置体验 |
| `cloud_only` | 纯云端 DeepSeek Flash/Pro（或兼容 OpenAI API） | 体验新模型、日常 PR 审阅、对外 PoC |
| `hybrid` | 本地 Ollama 压缩输入 + 云端生成审阅结论 | 长 PR、成本敏感、仍需云端推理质量 |
| `local_only` | 全程本地 Ollama | 保密研发、内网合规、数据不出域 |

**审阅深度**：`REVIEW_DEPTH_MODE`（`fast` / `balanced` / `deep`），选项见 `GET /api/review-depth-options`。

**Token 统计**：任务完成后结果含分 tier 的 prompt/completion 计数（云端与本地分列展示）。

**图表**：详情页四张 Mermaid 图（规则模式侧重规则报告与验真面板，见 [JUDGE_DEMO](./docs/JUDGE_DEMO.md)）。

默认规则包：`backend/app/rules/packs/default/`。

## 测试

```bash
# 后端
cd backend
# Windows: set PYTHONPATH=.
# Linux/macOS: export PYTHONPATH=.
pytest tests/ -v

# 前端
cd frontend
npm test -- --run
npm run build
```

或：`make test-backend` / `make test-frontend`。测试通过 `tests/conftest.py` **Mock** LLM，不消耗 API 额度。CI（GitHub Actions）同样仅跑 mock 测试。

## 开源借鉴与许可证

| 来源 | 许可证 | 本项目用法 |
|------|--------|------------|
| [Semgrep](https://github.com/semgrep/semgrep) | LGPL-2.1 | 仅借鉴 YAML 规则字段设计 |
| [reviewdog](https://github.com/reviewdog/reviewdog) | MIT | 仅借鉴 diff 范围与 severity |
| [Danger](https://github.com/danger/danger) | MIT | 仅借鉴 PR 上下文与 fail/warn 分级 |

本项目采用 [MIT License](./LICENSE)。
