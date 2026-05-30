# 单任务 Token 统计

## 字段说明

`TaskRecord.token_stats`（`TaskTokenStatsSchema`）：

| 字段 | 说明 |
|------|------|
| `cloud_*` | 云端 Flash/Pro 累计 |
| `local_*` | 本地 Ollama（压缩 + 纯本地推理）累计 |
| `total_tokens` | 云端 + 本地合计 |
| `estimated` | 任一调用缺少 API 精确 usage 时为 `true` |
| `by_tier` | 按 `flash` / `pro` / `local_compress` / `local_flash` / `local_pro` 明细 |
| `display_segments` | 详情页/导出用展示段（`label` 由后端单源生成） |

## 采集来源

- **云端**：OpenAI 兼容 API 响应 `usage.prompt_tokens` / `completion_tokens`
- **Ollama**：`prompt_eval_count` / `eval_count`；缺失时粗估并标 `estimated=true`

## 查看方式

```powershell
curl http://localhost:8000/api/tasks/<task_id>
```

任务详情页与「导出 Markdown」均读取 `display_segments`，前端不写死「云端/本地/合计」中文。

## 与 review_stats 区别

| 项 | review_stats | token_stats |
|----|--------------|-------------|
| 含义 | 调用次数、审阅覆盖 | Token 用量 |
| 位置 | `result.review_stats` | `TaskRecord.token_stats` |
