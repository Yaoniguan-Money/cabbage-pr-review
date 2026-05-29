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

启动后访问 http://localhost:8000/health ，应看到 `llm_enabled: true`、`use_mock_llm: false`、`model_profile: v4_flash_pro_via_env`。

未配置 Key 且 `USE_MOCK_LLM=false` 时，`POST /api/tasks` 返回 **503**（不再使用关键词/启发式 fallback 生成业务结论）。

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
