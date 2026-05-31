# 评委演示指南

> 主叙事：**纯规则模式（`rules_only`）** — 零 API Key、零 Ollama、零 Mock，由 YAML 规则引擎真实命中，输出 Markdown 报告与四张 Mermaid 可视化图。

## 四步体验

1. **启动（默认真实规则）**

   ```bash
   git clone <repo> && cd <repo>
   docker compose up --build
   # 或：.\scripts\start-demo.ps1（Windows） / make demo
   # 兼容：docker compose -f docker-compose.demo.yml up --build
   ```

   打开 http://localhost:8080 ，确认 http://localhost:8000/health 中：
   - `llm_mode` 为 `rules_only`、`use_mock_llm` 为 `false`
   - `rules_pack_loaded` 为 `true`、`rules_count` > 0、`rules_invalid_count` 为 `0`

2. **选择演示场景**

   在首页「评委演示 Patch」区域查看 **S1 / S2 / S3** 场景卡片（描述与预期 `rule_id` 由 `GET /api/demo-patches` 下发），点击「加载场景」。

   推理模式应保持 **纯规则**（由 `.env.demo` 的 `LLM_MODE=rules_only` 经 `GET /api/llm-mode-options` 默认选中）。

3. **开始分析**

   点击「开始分析」，详情页可查看：
   - **总览**：变更统计、四图预览、结构索引、规则命中验真面板
   - **示例图**：与云端模式共用 `DiagramCard` 渲染链
   - **规则报告** / **规则命中** / **变更概览**

4. **验真对照**

   总览页「规则命中验真」对照预期 `rule_id` 与实际命中；也可导出 Markdown。

## 演示场景与预期命中

| 场景 | 展示能力 | 预期 `rule_id` |
|------|----------|----------------|
| **S1 安全综合** | 多规则并行、HIGH severity | `patch-hardcoded-secret`、`eval-or-exec` |
| **S2 变更面** | `match.all`、CI/Docker 路径 | `dockerfile-changed`、`dockerfile-root-user`、`ci-config-changed` |
| **S3 工程治理** | 依赖与测试覆盖 | `lockfile-changed`、`requirements-unpinned`、`test-file-removed` |

Patch 与结构 sidecar：`data/demo/S*.patch` + `S*.context.json`（经 API 返回，不在前端写死）。

每个演示 Patch 体量门槛（`test_demo_alignment.py` 自动校验）：

- 整包 `+`/`-` 合计 **≥ 480 行**
- 变更文件 **≥ 8** 个，其中 **≥ 6** 个文件各自 diff **≥ 15 行**
- **≥ 2** 个文件含多个 `@@` hunk
- sidecar 中 `path_compare_focus` / `file_to_node` / `summary_line` 与 patch 路径对齐

## 架构约束（实施与答辩必读）

### 模块边界

| 模块 | 允许 | 禁止 |
|------|------|------|
| `backend/app/agents/` | LLM 编排、结构化 I/O | 业务 regex、风险关键词启发式 |
| `backend/app/rules/*.py` | 通用 DSL 求值 | 内联业务 `re.compile` pattern |
| `backend/app/rules/packs/` | 规则 id、pattern、severity | — |
| `backend/app/local/*_meta.py` | UI / 演示文案单源 | 审阅业务逻辑 |
| `frontend/` | 消费 API meta | 硬编码中文文案、演示 patch 正文 |
| `data/demo/` | 示例 Patch + context 数据 | 在 Python 中伪造命中 |

### 禁止硬编码

- 业务 **regex 仅存在于 YAML**（`packs/default/*.yaml`）。
- 表头、按钮、Mock 横幅等文案经 **`rule_meta` / `input_page_meta` / `client_meta` / `demo_patches_meta`** 暴露 API。
- 演示不得使用「假命中」逻辑冒充规则引擎；命中必须来自 `rule_evaluator` 对真实 patch 的求值。

### CI 门禁（克隆后可本地复现）

```bash
cd backend
set PYTHONPATH=.
pytest tests/test_rules_no_inline_patterns.py tests/test_no_heuristics.py tests/test_frontend_no_hardcode.py tests/test_rules_regression.py tests/test_demo_patches.py tests/test_demo_alignment.py tests/test_rules_diagrams.py -v
```

## 可选附录：Mock LLM UI

仅用于展示 LLM Agent 进度对照：

```bash
docker compose -f docker-compose.demo-mock.yml up --build
```

详情页会显示 **Mock 演示模式** 横幅（文案来自 `GET /api/client-meta` 的 `mock_mode_banner`）。

## 相关文档

- [README.md](../README.md) — 技术栈、推理模式与环境变量
- [CLOUD_DEPLOY.md](./CLOUD_DEPLOY.md) — 公网部署（评委自备 Key）

## Phase 2 能力（v2.5）

- **hunk 级 DiffAtom**：大文件多 hunk 独立命中（`split_patch_hunks: true`）
- **AST 规则**：`security.ast.yaml` 中 `python-bare-except` / `python-wildcard-import`（需 `tree-sitter` 依赖）
- **规则四图**：`rules_diagrams.py` + demo context sidecar，复用 `diagram_normalize` / `mermaid_render`
- 验收：`pytest tests/test_rules_hunk_diff.py tests/test_rule_ast.py tests/test_rules_diagrams.py -v`
