# v2.0 对齐合规自查表（第三轮归零）

更新时间：2026-05-29（第三轮实施）  
标准文档：[AI_PR_Review_助手执行计划_定稿_v2.0.md](../AI_PR_Review_助手执行计划_定稿_v2.0.md)

**结论：功能剩余差异清单 = 0 条**（Docker 守护进程未启动属**环境前置项**，见文末）。

---

## 第三轮复验命令与结果

| 命令 | 结果 |
|------|------|
| `cd backend && set PYTHONPATH=. && pytest tests/ -v` | **11 passed**（2026-05-29 本机） |
| `rg "RISK_KEYWORDS\|_heuristic\|diagram_from_modules" backend/app/agents` | **无匹配** |
| `cd frontend && npm run build` | **built in ~7.6s** |
| `docker compose build`（`pr/`） | **未通过**：Docker Desktop 守护进程未运行（`npipe://...dockerDesktopLinuxEngine` 不存在） |

---

## 逐项核对（§1～§11）

### §1 项目目标与定位

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 1.1 | 72h 可演示 MVP | 已完成 | `README.md` | 本地/Docker 启动 |
| 1.2 | 结构化审阅辅助 | 已完成 | `frontend/src/App.tsx` | 无自动 merge |
| 1.3 | 平衡版 | 已完成 | 三图 + LLM 风险 | 详情页总览 |

### §2 用户需求

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 2.1-2.3 | 五大核心问题 | 已完成 | Agent1-5 + `VisualizationSchema` | Patch/PR 任务结果 |

### §3 首发方案

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 3.1 | 三输入 + 公开 PR | 已完成 | `task_runner._prepare_context` | PR/Patch/LOCAL |
| 3.2 | Web 详情 + 异步轮询 | 已完成 | `DetailPage.tsx`, `task_store` | 创建任务轮询 |
| 3.3 | 默认摘要+三图+风险 | 已完成 | `DetailPage` overview Tab | 打开详情首屏 |
| 3.4 | 进度/置信度/图例 | 已完成 | `AgentProgressBar`, `GraphNode.confidence`, `mermaid_render` | 三图 JSON |
| 3.5 | 识别+重跑+补上下文一次 | 已完成 | Agent5 `detected_*`；`RerunPanel`；`tasks.py` `rerun_used` | 重跑限制 1 次 |
| 3.6 | 示例 + 导出 | 已完成 | `examples.py`, `export_md.py` | `GET .../export` |
| 3.7 | GitHub 只读、内存态 | 已完成 | 无写回 API；`TaskStore` | 无 DB |

### §4 架构

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 4.1 | DeepSeek 主能力 + 结构化 JSON | 已完成 | `llm_helpers.py`；五 Agent 仅 `call_*_json` | 无启发式 fallback |
| 4.1 | LangGraph 编排 | 已完成 | `graph/workflow.py` | `test_workflow.py` |
| 4.1 | 局部降级（空 schema） | 已完成 | `workflow.py` except → 空结构 + `degradation_notes` | 无假业务数据 |
| 4.2 | 主流程 | 已完成 | `task_runner.py`, `tasks.py` | E2E PR（需 Key） |

### §5 五个 Agent

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 5.1 | Agent1 base 全文 | 已完成 | `git_workspace.read_files_at_ref` → `base_file_contents`；`agent1_base_scan.py` | `test_git_workspace.py` |
| 5.2 | Agent2 head 全文 | 已完成 | `head_file_contents`；`agent2_head_scan.py` | `test_agents.py` version=head |
| 5.3 | Agent3 四级差异 + 影响图 | 已完成 | `agent3_diff.py` + LLM `impact_diagram` | fixture `diff_compare.json` |
| 5.4 | Agent4 递进 Pro 多轮 | 已完成 | `AtomContextPlanBatch` → 读文件 → `RiskReviewSchema`；`MAX_DEPTH=2` | `agent4_review.py` |
| 5.5 | Agent5 三图 nodes/edges | 已完成 | `agent5_visualize.py` + `diagram_utils.attach_mermaid` | fixture 三张图 |

### §6 生成策略

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 6.1 | AI 出结构 → 模板渲染 Mermaid | 已完成 | `mermaid_render.render_diagram` | 无 `diagram_from_modules` |
| 6.2 | 风险 JSON + 前端渲染 | 已完成 | `RiskReviewSchema`, `RiskList.tsx` | evidence 字段 |
| 6.3 | 降级说明 | 已完成 | `degradation_notes`；503 无 Key | `llm_guard.py` |

### §7 技术栈

| ID | 定稿要求 | 状态 | 证据 | 验证 |
|----|----------|------|------|------|
| 7.3 | Flash 1/2/3/5，Pro 4 | 已完成 | `DEEPSEEK_FLASH_MODEL` / `DEEPSEEK_PRO_MODEL` | `GET /health` |
| 7.4 | 结果修复 | 已完成 | `llm_helpers` → `repair_model` | 每次 Flash/Pro 成功路径 |
| 7.7 | Docker | 部分（环境） | `docker-compose.yml`；`backend/Dockerfile` 含 `git` | 见环境前置项 |

### §8～§11

| 章节 | 状态 | 证据 |
|------|------|------|
| §8 Mermaid 主用 | 已完成 | `mermaid_render.py` |
| §9 JSON schema + 重试 | 已完成 | `schemas.py`；2 次重试 + `repair_model` |
| §10 测试 | 已完成 | `tests/` 11 项；`conftest.py` Mock LLM |
| §11 明确不做 | 已完成 | 无私有库/DB/回写 |

---

## 禁止业务硬编码（验收口径）

| 检查项 | 结果 |
|--------|------|
| `backend/app/agents` 无 `RISK_KEYWORDS` / `_heuristic` / `diagram_from_modules` | 通过（`test_no_heuristics.py`） |
| 无 `call_*_json(..., fallback=...)` | 通过（`llm_helpers.py`） |
| `project_detect` 未接入主链路 | 通过（模块已 `NotImplementedError` 弃用） |
| base/head 文件来自 git | 通过（`git_workspace.py` + `task_runner`） |

---

## 剩余差异清单

**0 条**（功能与定稿对齐项均已闭合）。

---

## 环境前置项（非功能未完成）

| 项 | 说明 | 验收人操作 |
|----|------|------------|
| E-01 Docker 守护进程 | 本轮 `docker compose build` 失败：Engine 未运行 | 启动 Docker Desktop 后执行 `docker compose up --build`，访问 :8080 / :8000/health |
| E-02 DeepSeek 生产 Key | 真实 PR 分析需 `.env` 中 `DEEPSEEK_API_KEY` + `USE_MOCK_LLM=false` | `POST /api/tasks` 不应 503 |
| E-03 本机 git | PR URL clone 与 `test_git_workspace` 依赖 git CLI | `git --version` |

---

## 验收人最小步骤（可复现）

1. `cd backend && set PYTHONPATH=. && pytest tests/ -v` → 11 passed  
2. `rg "RISK_KEYWORDS|_heuristic|diagram_from_modules" backend/app/agents` → 无输出  
3. 配置 `.env` 后 `uvicorn app.main:app --port 8000`，`curl http://localhost:8000/health`  
4. 提交 Patch 任务 → 详情页总览含摘要、三图、风险（`degradation_notes` 无「启发式」）  
5. （可选）公开 PR：抽样 `base_file_contents` 与 `git show <base_sha>:path` 一致  

---

上一轮差异（R-01～R-08）闭合说明见 [V2_REMAINING_GAPS.md](./V2_REMAINING_GAPS.md) 历史记录；**以本文件为准**。
