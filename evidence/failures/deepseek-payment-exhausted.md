# Rejected DeepSeek pilot: payment exhausted

- 模型：`deepseek-v4-flash`，live provider。
- 结果：50 个预定 case 中 14 success、36 failed；失败均包含 HTTP 402 Payment Required。
- 当时旧数据顺序先 positive 后 negative，余额耗尽与标签顺序相关；旧 scorer 还会把 provider failure 当作 negative prediction。因此对应 confusion matrix/F1 在统计上无效，不能用于模型质量或简历结论。
- 保留文件：`../raw/pr_review_deepseek_payment_exhausted_pilot.json`、`../raw/pr_review_deepseek_payment_exhausted_metrics.json`、`pr_review_deepseek_payment_exhausted_failures.jsonl`。
- 没有删除 36 个失败，也没有用前 14 个成功样本做选择性指标。
- 后续修复：数据固定 shuffle；Qwen 在同一完整 50-case 顺序 50/50 成功；当前 scorer 将 provider failure 单独报告；永久 HTTP 错误不重试。
