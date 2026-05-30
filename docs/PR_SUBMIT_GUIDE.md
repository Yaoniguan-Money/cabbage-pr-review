# 分支提交与 PR 拆分建议

面向 `feat/task-token-stats` 等工作区改动，避免与已合并 PR 重复或混杂审查主题。

## 推荐拆分

| PR | 主题 | 主要文件 |
|----|------|----------|
| PR7 | 单任务 Token 统计 | `token_usage.py`、`schemas` `TaskTokenStats`、`task_runner`、providers、`DetailPage`、`export_md`、`docs/TOKEN_STATS.md`、相关测试 |
| Hotfix | Mermaid 保留字节点 ID | `mermaid_render.py`、`test_mermaid_render.py` |
| 质量小改 | 审阅深度 `cost_tier_label`、死代码清理 | `review_depth.py`、`InputPage.tsx`、`test_frontend_no_hardcode.py` |

也可合并为 **一个 PR**，在描述中用三节说明上述范围。

## 勿重复提交

- PR #5（`package-lock` / `esbuild`）已进 `main`，勿再改 lock 除非 CI 再次失败。
- PR #6（v2.2 LLM 模式）已进 `main`，新 PR 仅包含 Token / Mermaid / 质量小改增量。

## 提交前自检

```powershell
cd backend
$env:PYTHONPATH="."
pytest tests/ -v

cd ..\frontend
npm run build
npm test -- --run
```

## 推送（需用户手动执行）

```powershell
git push -u origin feat/task-token-stats
gh pr create --title "..." --body "..."
```

代理不会自动 `commit` / `push` / 开 PR，除非明确要求。
