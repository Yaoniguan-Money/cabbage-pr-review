# 评委演示指南

> 主叙事：**纯规则模式（`rules_only`）** — 零 API Key、零 Ollama、零 Mock，由 YAML 规则引擎真实命中并生成 Markdown 报告。

## 三步体验

1. **启动（默认真实规则）**

   ```bash
   git clone <repo> && cd <repo>
   docker compose -f docker-compose.demo.yml up --build
   ```

   打开 http://localhost:8080 ，确认 http://localhost:8000/health 中：
   - `llm_mode` 为 `rules_only`、`use_mock_llm` 为 `false`
   - `rules_pack_loaded` 为 `true`、`rules_count` > 0、`rules_invalid_count` 为 `0`

2. **加载演示 Patch**

   在首页「评委演示 Patch」区域点击 **S1 / S2 / S3** 之一（文案与 patch 内容由 `GET /api/demo-patches` 下发，前端不得硬编码）。

   推理模式应保持 **纯规则**（由 `.env.demo` 的 `LLM_MODE=rules_only` 经 `GET /api/llm-mode-options` 默认选中）。

3. **查看结果**

   点击「开始分析」，进入详情页打开 **规则报告** 页签（Markdown 报告 + 结构化规则命中表格，含「规则说明」列），对照下表 `rule_id` 验证命中是否为真实规则引擎输出。

## 演示场景与预期命中

| 场景 | 展示能力 | 预期 `rule_id` |
|------|----------|----------------|
| **S1 安全综合** | 多规则并行、HIGH severity | `patch-hardcoded-secret`、`eval-or-exec` |
| **S2 变更面** | `match.all`、CI/Docker 路径 | `dockerfile-root-user`、`ci-config-changed` |
| **S3 工程治理** | 依赖与测试覆盖 | `lockfile-changed`、`requirements-unpinned`、`test-file-removed` |

Patch 源文件：`data/demo/S*.patch`（经 API 返回，不在前端写死）。

## 架构约束（实施与答辩必读）

### 模块边界

| 模块 | 允许 | 禁止 |
|------|------|------|
| `backend/app/agents/` | LLM 编排、结构化 I/O | 业务 regex、风险关键词启发式 |
| `backend/app/rules/*.py` | 通用 DSL 求值 | 内联业务 `re.compile` pattern |
| `backend/app/rules/packs/` | 规则 id、pattern、severity | — |
| `backend/app/local/*_meta.py` | UI / 演示文案单源 | 审阅业务逻辑 |
| `frontend/` | 消费 API meta | 硬编码中文文案、演示 patch 正文 |
| `data/demo/` | 示例 Patch 数据 | 在 Python 中伪造命中 |

### 禁止硬编码

- 业务 **regex 仅存在于 YAML**（`packs/default/*.yaml`）。
- 表头、按钮、Mock 横幅等文案经 **`rule_meta` / `input_page_meta` / `client_meta` / `demo_patches_meta`** 暴露 API。
- 演示不得使用「假命中」逻辑冒充规则引擎；命中必须来自 `rule_evaluator` 对真实 patch 的求值。

### CI 门禁（克隆后可本地复现）

```bash
cd backend
set PYTHONPATH=.
pytest tests/test_rules_no_inline_patterns.py tests/test_no_heuristics.py tests/test_frontend_no_hardcode.py tests/test_rules_regression.py tests/test_demo_patches.py -v
```

## 可选附录：Mock LLM UI

仅用于展示完整 Agent 进度与 Mermaid 四图，**不代表规则引擎质量**：

```bash
docker compose -f docker-compose.demo-mock.yml up --build
```

详情页会显示 **Mock 演示模式** 横幅（文案来自 `GET /api/client-meta` 的 `mock_mode_banner`）。

## 相关文档

- [V2.4_RULES_MODE.md](./V2.4_RULES_MODE.md) — 纯规则模式操作手册
- [RULES_ENGINE_REVIEW.md](./RULES_ENGINE_REVIEW.md) — 规则引擎架构审阅

## Phase 2 能力（v2.5）

- **hunk 级 DiffAtom**：大文件多 hunk 独立命中（`split_patch_hunks: true`）
- **AST 规则**：`security.ast.yaml` 中 `python-bare-except` / `python-wildcard-import`（需 `tree-sitter` 依赖）
- 验收：`pytest tests/test_rules_hunk_diff.py tests/test_rule_ast.py -v`
