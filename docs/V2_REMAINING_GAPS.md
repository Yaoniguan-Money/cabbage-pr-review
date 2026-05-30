# v2.0 对齐自查与剩余差异清单（历史归档）

> **第三轮已归零**：请以 [V2_COMPLIANCE.md](./V2_COMPLIANCE.md) 为准（剩余差异 = 0）。

更新时间：2026-05-29（第二轮修复后，已 superseded）  
标准文档：[AI_PR_Review_助手执行计划_定稿_v2.0.md](../AI_PR_Review_助手执行计划_定稿_v2.0.md)

**历史结论（第二轮）：剩余差异清单 ≠ 0（共 7 项，R-01～R-05、R-07、R-08）。第三轮已全部闭合。**

---

## 复验命令与结果（证据）

| 命令 | 结果 |
|------|------|
| `cd backend && set PYTHONPATH=. && pytest tests/ -v` | **10 passed**（2026-05-29 本机） |
| `cd frontend && npm run build` | **built in ~7.5s**（此前构建通过） |
| `GET http://localhost:8000/health` | 需启动后验证 `llm_enabled` / `use_mock_llm` |
| `docker compose up --build` | **本轮未在 CI 容器内执行**，需验收人本地验证 |

---

## 逐项核对表

### §1 项目目标与定位

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 1.1 | 72h 可演示 MVP | **已完成** | 仓库可运行；`README.md` 启动说明 |
| 1.2 | 结构化审阅辅助，非替代终审 | **已完成** | 产品文案 `frontend/src/App.tsx`；无自动 merge/approve |
| 1.3 | 平衡版 | **已完成** | 三图 + 规则/LLM 混合分析 |

### §2 用户需求

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 2.1-2.3 | 五大核心问题 | **部分完成** | 摘要/风险/缺失信息覆盖；契约级影响依赖 patch 粒度 **→ R-03** |

### §3 首发方案

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 3.1 | Py+TS/JS；FastAPI/Express/React；公开 PR；三输入 | **部分完成** | 三输入 `task_runner._prepare_context`；框架识别为关键词 **→ R-03** |
| 3.1 | 输入优先级：先 PR URL | **已完成** | `InputPage.tsx` 默认 tab `pr_url` |
| 3.2 | Web+详情；三卡片；左 nav；异步+轮询；单任务串行 | **已完成** | `InputPage`/`DetailPage`；`task_store.run_exclusive`；`astream` 逐步进度 |
| 3.3 | 默认展示摘要+三图+风险 | **已完成** | `DetailPage` 默认「总览」含摘要+三图预览+风险前5条 |
| 3.4 | Agent1-5 进度；路径图/风险置信度；缺失区块；图例统一；风险排序 | **部分完成** | `AgentProgressBar`；`RiskList` 排序；`mermaid_render` classDef；路径图节点 `confidence` **→ R-07** |
| 3.5 | 自动识别+手动切换；1-3 差异点重跑；补上下文仅一次 | **已完成** | Agent5 `detected_*`；`RerunPanel`；`tasks.py` `rerun_used` |
| 3.6 | 示例 PR；Markdown 导出 | **已完成** | `examples.py`；`export_md.py` |
| 3.7 | GitHub 只读；内存态；无历史 | **已完成** | 无 comment API；`TaskStore` 内存；无 DB |

### §4 架构

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 4.1 | DS V4 主能力 | **部分完成** | `llm/client.py`；模型名见 **→ R-01** |
| 4.1 | 本地能力为辅 | **已完成** | `local/*`；`ollama_provider.py`（v2.2） |
| 4.1 | LangGraph 编排 | **已完成** | `graph/workflow.py` |
| 4.1 | 全 Agent 结构化 JSON | **部分完成** | Pydantic schema；无 Key 时启发式 **→ R-02** |
| 4.1 | 局部降级 | **已完成** | `workflow.py` try/except；`llm_helpers` 降级 notes |
| 4.2 | 主流程 | **已完成** | `task_runner.py` + API `tasks.py` |

### §5 五个 Agent

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 5.1 | Agent1：README+目录+入口+base 代码 | **部分完成** | `context_builder.build_version_scan_context(version=base)`；`github` readme+base_tree；非 git checkout 全文件 **→ R-03** |
| 5.2 | Agent2：head 版本 | **部分完成** | `version=head`+`head_tree`+head patch 片段；同 **→ R-03** |
| 5.3 | Agent3：四级差异+差异原子 | **已完成** | `agent3_diff.py` file/func/route/dep + `DiffCompareSchema` |
| 5.4 | Agent4：递进审阅+2 层上下文 | **部分完成** | `_layer1_context`/`_layer2_context`+`MAX_DEPTH=2`；非 AST 调用图 **→ R-04** |
| 5.5 | Agent5：VisualizationSchema+三图 | **已完成** | `VisualizationSchema`+`agent5_visualize.py` |

### §6 生成策略

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 6.1 | 路径图：结构化数据+模板渲染 | **已完成** | `agent5._build_path_compare` + `mermaid_render` |
| 6.2 | 风险：Agent4 JSON+程序渲染 | **已完成** | `RiskList.tsx` |
| 6.3-6.5 | 降级/识别/README | **见上** | |

### §7 技术栈

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 7.1-7.2 | FastAPI/LangGraph/React/Vite | **已完成** | 工程结构 |
| 7.3 | Flash:1/2/3/5 Pro:4 | **部分完成** | `llm_helpers.call_flash_json`/`call_pro_json`；模型名 **→ R-01** |
| 7.4 | 本地层：缓存/规则/渲染/预留模型 | **部分完成** | `cache.py`/`mermaid_render`/`ollama_provider.py`；无 result_repair 调用链 **→ R-05** |
| 7.5-7.7 | 内存/MD/Docker | **部分完成** | 内存 OK；Docker **→ R-08** |

### §8 参考开源

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 8.7 | Mermaid 主用；Graphviz 预留 | **部分完成** | `mermaid_render.py`；`graphviz_render.py` 仅占位 **→ R-08** |

### §9 JSON 规范

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 9 | 每 Agent schema+失败重试 | **部分完成** | `schemas.py`；`llm_helpers` 重试 1 次；无 Key 走启发式 **→ R-02** |

### §10 测试

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 10.2 | 输入解析/schema/导出 | **已完成** | `tests/test_*.py` 共 10 项 |

### §11 明确不做

| ID | 定稿要求 | 状态 | 证据 |
|----|----------|------|------|
| 11 | 不回写/无私有库/无 SQLite 等 | **已完成** | 代码库无对应实现 |

---

## 第二轮已修复项（对照上一轮验收）

| 问题 | 修复 | 证据文件 |
|------|------|----------|
| Agent1/2 未分 base/head | `context_builder.build_version_scan_context` + GitHub `base_tree`/`head_tree` | `context_builder.py`, `github.py` |
| README 未注入 | `readme` 进入 scan_ctx；`ProjectIndexSchema.readme_excerpt` | `agent1_base_scan.py` |
| 仅 Agent4 调 LLM | 五 Agent 均 `call_flash_json`/`call_pro_json`+降级 | `agent1-5`, `llm_helpers.py` |
| 进度一次性更新 | `workflow_app.astream` 逐节点更新 | `task_runner.py` |
| 补上下文未读文件 | `load_extra_context_files` | `context_builder.py`, `agent4_review.py` |
| 风险无 evidence | `RiskItem.evidence/suggestion` | `schemas.py`, `RiskList.tsx` |
| 路径图无置信度 | `GraphNode.confidence` on path_compare | `agent5_visualize.py` |

---

## 剩余差异清单（必须逐项验收）

### R-01 DeepSeek「V4 Flash / V4 Pro」型号名与 API 实型不一致

- **定稿**：§7.3 明确 V4 Flash / V4 Pro。  
- **现状**：环境变量默认 `deepseek-chat` / `deepseek-reasoner`（`config.py`）。  
- **验证**：查看 `.env` 与 `GET /health` 返回的 `deepseek_model_*`。  
- **若要归零**：在 DeepSeek 控制台确认 V4 对应 model id 后写入 `.env`，并更新文档截图。

### R-02 无 API Key 时 Agent 输出为启发式，非云端 JSON

- **定稿**：§4.1、§9 要求 DS 为主能力、按 schema 调模型。  
- **现状**：`USE_MOCK_LLM=true` 或 Key 为空时，`llm_helpers` 走 `fallback()`（`llm_helpers.py` L17-20）。  
- **验证**：无 Key 跑任务，结果与有 Key 时来源不同；`degradation_notes` 含「未启用」类说明。  
- **若要归零**：验收环境必须配置有效 `DEEPSEEK_API_KEY` 且 `USE_MOCK_LLM=false`（功能上对齐；无 Key 场景属降级，定稿 §6.3 允许）。

### R-03 base/head「完整代码」非 git checkout 级，而为 patch 片段 + Git tree 路径

- **定稿**：§5.1/5.2 输入含 base/head 版本代码。  
- **现状**：`code_snippets` 来自 patch 增删行；GitHub 提供 `base_tree`/`head_tree` 路径列表，不拉取每个文件全文。  
- **验证**：对比 `ProjectIndexSchema.code_snippets` 与仓库 checkout 文件。  
- **若要归零**：需增加 `git clone` + checkout base/head SHA 读文件（超出当前 MVP 实现范围）。

### R-04 Agent4「递进深挖」为规则分层拼上下文，非语义调用图扩展

- **定稿**：§5.4 发现新问题继续深挖、最多 2 层。  
- **现状**：`_layer1_context`（同模块 snippet）+ `_layer2_context`（入口/route）；`MAX_DEPTH=2` 常量。  
- **验证**：阅读 `agent4_review.py`；无动态新差异点发现循环。  
- **若要归零**：需实现差异点队列 + 每层触发新 atom 的迭代（未实现）。

### R-05 本地能力层「结果修复」未接入主链路

- **定稿**：§7.4 结果修复。  
- **现状**：`local/result_repair.py` 存在但无 Agent 调用。  
- **验证**：`rg repair_model backend/app` 仅 hit 定义处。

### R-06 ~~详情页默认同时展示~~（已修复）

- **修复**：`DetailPage.tsx` 增加 `overview` 默认 Tab。  
- **验证**：打开详情页首屏可见摘要 + 三图预览 + 风险前 5 条。

### R-07 架构图/影响图节点未统一展示置信度（仅路径对比图部分节点有）

- **定稿**：§3.4 关键路径图和风险项置信度。  
- **现状**：风险列表有 `confidence`；路径图部分 `GraphNode.confidence`；架构/影响图 primarily `risk` level only。  
- **验证**：检查三张图 JSON 字段。

### R-08 Docker Compose 一键启动未在本轮自动化验证

- **定稿**：§7.7。  
- **现状**：`docker-compose.yml` 存在。  
- **验证**：验收人执行 `docker compose up --build` 并访问 :8080/:8000。  

---

## 剩余差异计数

| 类别 | 数量 |
|------|------|
| **未完成（需产品/架构扩展）** | R-03, R-04 |
| **部分完成（可配置或 UI 可改）** | R-01, R-02, R-05, R-07, R-08 |
| **合计未归零** | **7** |

---

## 验收人最小验证步骤（可复现）

1. 配置 `pr/.env`：`DEEPSEEK_API_KEY` + `USE_MOCK_LLM=false`  
2. `cd backend && pip install -r requirements.txt && set PYTHONPATH=. && uvicorn app.main:app --port 8000`  
3. `cd frontend && npm run dev` → http://localhost:5173  
4. Patch 输入含 FastAPI 路由的 diff → 完成 → 检查三图、风险 evidence、导出 MD  
5. `pytest tests/ -v` → 10 passed  

---

**声明：在未完成 R-01～R-08 归零或书面接受前，不得宣称「与 v2.0 完全一致」。**
