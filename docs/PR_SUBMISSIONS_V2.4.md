# v2.3.1 / v2.4 PR 提交说明

按「每个 PR 只做一件事」拆分为 **4 个堆叠 PR**，请按顺序创建并合并（后者 base 为前者分支）。

---

## PR 1：v2.3.1 四图（若尚未合并）

**分支**：`feat/v2.3.1-global-compare` → `main`  
**链接**：https://github.com/Yaoniguan-Money/cabbage-pr-review/compare/main...feat/v2.3.1-global-compare

### 标题

feat(v2.3.1): 新增 global_compare 四图与 diagram_meta 单源

### 功能描述

在审阅结果中增加第四张「全局架构前后对比图」，图表标题、图例与 Mermaid 样式由 `diagram_meta` 单源下发，前端不再硬编码图表文案。

### 实现思路

- 扩展 `VisualizationSchema` 与 Agent5 指令，固定四张 `diagram_type`
- `diagram_meta.py` 集中管理类型元数据、样式 token、UI 字符串
- 新增 `/api/diagram-meta` 供前端渲染

### 测试方式

```powershell
cd backend && pytest tests/test_diagram_meta.py tests/test_mermaid_render.py -q
cd frontend && npm test -- --run MermaidDiagram DetailPage
docker compose up -d
# 创建 cloud_only 任务，详情页应展示四张图
```

---

## PR 2：v2.4 纯规则引擎（后端）

**分支**：`feat/v2.4-rules-engine` → `feat/v2.3.1-global-compare`（v2.3.1 合并后改 base 为 `main`）  
**链接**：https://github.com/Yaoniguan-Money/cabbage-pr-review/compare/feat/v2.3.1-global-compare...feat/v2.4-rules-engine

### 标题

feat(v2.4): 纯规则审阅引擎与 workflow 双 pipeline

### 功能描述

新增 `rules_only` 推理模式：零 LLM，由可配置 YAML 规则包审阅 PR，输出 Markdown 报告。创建任务时选择「纯规则」即可使用，无需 Cloud API Key 与 Ollama。

### 实现思路

- `app/rules/`：规则加载、评估、diff/review/markdown pipeline
- `workflow_helpers` + `pipeline_dispatch`：LangGraph 节点在 LLM / 规则双 pipeline 间分发
- `llm_mode.py` 增加第四档 `rules_only`；`/api/rules-meta` 暴露 UI 文案
- `export_md`、任务校验与 health 扩展规则包状态

### 测试方式

```powershell
cd backend && pytest tests/test_rules_engine.py tests/test_workflow_rules_only.py tests/test_rules_linkage.py tests/test_llm_mode.py -q
curl http://localhost:8000/api/rules-meta
curl http://localhost:8000/health   # rules_pack_loaded, rules_count
# POST /api/tasks  llm_mode=rules_only, input_type=patch + 含 secret 的 diff
```

---

## PR 3：UI meta API 单源（后端）

**分支**：`feat/v2.4-ui-meta-api` → `feat/v2.4-rules-engine`  
**链接**：https://github.com/Yaoniguan-Money/cabbage-pr-review/compare/feat/v2.4-rules-engine...feat/v2.4-ui-meta-api

### 标题

feat(v2.4): UI 文案 meta API 单源（input/client/diagram）

### 功能描述

为输入页、API 客户端错误提示、详情页导航等提供后端单源文案，避免前端硬编码；扩展 `diagram_meta` 与 `rules-meta` 字段。

### 实现思路

- 新增 `input_page_meta.py`、`client_meta.py` 及 `/api/input-page-meta`、`/api/client-meta`
- 扩展 `diagram_meta`（节点摘要文案、概览风险条数等）
- 扩展 `rule_meta` 详情页 banner / 导航文案
- 审计测试 `test_frontend_no_hardcode`、`test_diagram_no_hardcode` 防止回归

### 测试方式

```powershell
cd backend && pytest tests/test_input_page_meta_api.py tests/test_client_meta_api.py tests/test_frontend_no_hardcode.py -q
curl http://localhost:8000/api/input-page-meta
curl http://localhost:8000/api/client-meta
```

---

## PR 4：前端联动与可用性（前端）

**分支**：`feat/v2.4-frontend-linkage` → `feat/v2.4-ui-meta-api`  
**链接**：https://github.com/Yaoniguan-Money/cabbage-pr-review/compare/feat/v2.4-ui-meta-api...feat/v2.4-frontend-linkage

### 标题

feat(v2.4): 规则模式信噪比优化与规则命中前端联动

### 功能描述

- **信噪比（零硬编码）**：调高 `large-patch-hunk` 阈值、收紧 `test-file-removed`、收窄 `route-decorator-changed`；按 `rule_id` 聚合 `risks`；证据拼接 `atom.summary`
- **引擎**：metadata 比率键、`rules_aggregate`、可选 `rules_preflight`；`rules_only` KPI 与 `quality_thresholds.rules_only.example.json`
- **前端**：`RuleHitsPanel` 按规则分组/折叠 LOW；`rules_only` Markdown 报告；输入页 meta 联动

### 实现思路

- `MarkdownReport`、`llmModeAvailability`、`pickInitialLlmMode`
- `client.ts`：`fetchClientMeta` + 统一 `throwApiError`
- `InputPage` / `DetailPage` / `DiagramCard` 仅渲染 API 字段，加载中显示 skeleton

### 测试方式

```powershell
cd frontend && npm test -- --run DetailPage InputPage pickInitialLlmMode MermaidDiagram
docker compose up -d
# 8080 输入页：混合模式在 Ollama 关闭时仍可点选并显示提示
# 创建 rules_only 任务，详情页展示 Markdown 报告 Tab
```

---

## 合并顺序

```
main ← PR1 (v2.3.1)
  ← PR2 (rules-engine)
    ← PR3 (ui-meta-api)
      ← PR4 (frontend-linkage)
```

PR2–PR4 合并前请将 base branch 更新为已合并的上游（GitHub 上 Edit base 或 rebase）。

## 未纳入提交

- `backend/rules/`：遗留 duplicate 目录，未提交
- `frontend/tsconfig.tsbuildinfo`：构建产物，未提交
- 备份 ref：`refs/backup/pre-split-v24`
