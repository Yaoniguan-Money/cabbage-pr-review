# AI PR Review 助手

基于定稿 v2.0 的 MVP：结构化 PR 影响分析与审阅辅助工具。

## 功能

- 三种输入：GitHub PR URL、Patch/Diff、本地仓库路径
- LangGraph 编排 5 个 Agent（原版本扫描 → PR 扫描 → 差异对比 → 递进审阅 → 可视化）
- 结果页：摘要条、三张 Mermaid 图、风险列表、缺失信息
- 支持一次补上下文重跑、Markdown 导出
- 局部降级：单 Agent 失败不阻断整体

## 快速启动

### 本地开发

```bash
# 后端
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

## 文档依据

- 主执行：[AI_PR_Review_助手执行计划_定稿_v2.0.docx](./AI_PR_Review_助手执行计划_定稿_v2.0.docx)
- 补充：[AI_PR_Review_助手执行计划_定稿_v2.0.md](./AI_PR_Review_助手执行计划_定稿_v2.0.md)

冲突时以 v2.0 为准。
