# AI PR Review 助手

结构化 PR 影响分析与审阅辅助工具：LangGraph 编排五个 Agent（原版本扫描 → PR 扫描 → 差异对比 → 递进审阅 → 可视化），并支持 **纯规则模式**（`rules_only`）零 API Key 演示。

> **交付说明**：最终提交 `chore: 发布前清理…` 仅移除文档与临时文件，**未改写**此前任何 commit；完整开发记录见 GitHub **Commits** / **Pull requests**。对外交付以 `main` 分支最新提交为准。

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
DEEPSEEK_FLASH_MODEL=deepseek-chat
DEEPSEEK_PRO_MODEL=deepseek-reasoner
USE_MOCK_LLM=false
LLM_MODE=cloud_only
```

启动后 http://localhost:8000/health 应见 `llm_enabled: true`。未配置 Key 且选择 **纯云端** 时 `POST /api/tasks` 返回 **503**；前端会优先引导 **纯规则**。

**依赖**：本机与镜像均需 **git**（PR URL 分析用 `git show`）。分析 GitHub PR 建议配置 `GITHUB_TOKEN`，否则易 403 限流。

## 公网部署（评委自备 API Key）

**阿里云 ECS（无域名先用 IP:8080）**：见 [docs/ALIYUN_DEPLOY.md](./docs/ALIYUN_DEPLOY.md)，服务器一键：`./scripts/aliyun-setup-demo.sh`。

**自有域名 + HTTPS**：服务器**不托管**个人 Key，步骤见 [docs/CLOUD_DEPLOY.md](./docs/CLOUD_DEPLOY.md)。

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

首页选项由 `GET /api/llm-mode-options` 下发（前端不硬编码文案）：

| `LLM_MODE` | 说明 |
|------------|------|
| `rules_only` | 纯 YAML 规则，零 LLM；适合演示与 CI |
| `cloud_only` | 纯云端 DeepSeek Flash/Pro |
| `hybrid` | 本地 Ollama 压缩 + 云端审阅结论 |
| `local_only` | 纯本地模型 |

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
