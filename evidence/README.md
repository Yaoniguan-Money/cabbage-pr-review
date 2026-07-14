# AI PR Review evidence package

本目录保存 2026-07-14 的固定数据集、规则基线、真实 provider 结果、失败试跑、测试、环境与复现入口。结论只覆盖“给定 unified diff 的单次结构化缺陷审阅组件”，不代表完整多 Agent 产品、生产流量或人工采纳率。

## 已批准指标（A-qualified）

在 50 个不同的 SWE-bench Lite Issue–PR 对上，构造 25 个反向 gold-fix 缺陷 patch 与 25 个正向 gold-fix 控制 patch。默认规则基线 TP/FP/FN/TN=0/1/25/24，P/R/F1=0/0/0；live `qwen-plus` 为 24/21/1/4，P/R/F1=53.33%/96.00%/68.57%。25 个正例的文件与行定位率均为 96%，但负例 flag rate 为 84%，平均每个负例 1.4 条误风险。因此该指标只能带着高误报限定使用。

候选简历句：

> 在 50 个固定 SWE-bench Lite Issue–PR 对（25 个反向 gold-fix 缺陷、25 个正向 gold-fix 控制）上，对比静态规则与单次 live Qwen 审阅；Qwen 缺陷检测 P/R/F1 为 53.33%/96.00%/68.57%，正例文件/行定位率均为 96%，并完整保留 84% 负例误报率、失败样本、延迟与 token 成本。

这句话尚未写入正式简历，只登记在 evidence 与 `_career_audit`。

## 数据集与标注

- 上游：[SWE-bench Lite 官方说明](https://www.swebench.com/lite.html)与[固定 Hugging Face 数据集](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite)。官方将 Lite 描述为 300 个 Issue–PR 对；本实验固定其中 50 个不同实例。
- 固定 revision：`69611d31007e1c6731db8bd5b5c3f2d33f5bab6e`。
- 上游 parquet SHA-256：`f46f2e3f003f2552932393da4b223e1e0456a2c71eba8b73ae58f29646c1278b`。
- 上游 parquet 在复现时下载到 `evidence/source/` 并校验上述 SHA；该可下载副本不进入 Git，以避免重复提交上游数据。
- 当前 JSONL SHA-256：见 `dataset-manifest.json`，由验证器逐次校验。
- 正例：把官方 gold fix patch 反向，得到会重新引入目标 issue 缺陷的 patch；每类 5 个，共 security、logic、exception、compatibility、performance 五类。
- 负例：另外 25 个不同实例的官方正向 gold fix；标签只表示“不含该来源 issue 的目标缺陷”，不保证没有任何无关缺陷。
- source tracker 链接指向实例 issue，不冒充精确 PR URL；“Issue–PR 对及 gold patch”的依据来自固定 SWE-bench 行。
- reviewer 只看到中性标题和 patch，不看到 issue 文本、构造方向、标签、严重级别或 gold location。
- `scripts/generate_demo_patches.py` 生成的 S1/S2/S3 演示样本明确排除在质量实验之外，因为它们带有已知规则命中目标。

## 指标定义

- Patch detection：返回至少一条结构化 risk 即判为 positive。
- File localization：至少一条 risk 的路径与 gold changed file 精确相等。
- Line localization：在正确文件中，risk 的闭区间行号与反向 patch 的精确 changed new-file 行至少重叠一行。
- Severity/category：在 gold 文件已定位的 risk 中匹配标注值。
- Clean-control flag rate：25 个控制 patch 中返回至少一条 risk 的比例。
- False risks/control：控制 patch 上返回的 risk 总数除以 25。
- Provider 失败单独计数，绝不当作 negative prediction。
- 延迟 P50/P95：对全部成功 per-patch 调用使用 nearest-rank percentile；失败调用只进入失败率，不进入延迟分位数。

## 结果入口

- 完整逐 case 数据：`datasets/pr_review_cases.jsonl` 与 `datasets/patches/`。
- 规则原始输出：`raw/pr_review_rules.json`。
- Qwen live 原始输出：`raw/pr_review_live_qwen.json`。
- 汇总和逐 case 打分：`raw/pr_review_metrics.json`。
- 所有 FN/FP：`failures/pr_review_failures.jsonl`。
- DeepSeek 余额失败试跑：`raw/pr_review_deepseek_payment_exhausted_pilot.json`、对应 metrics 与 failures；不进入批准指标。
- 测试：`raw/backend-pytest.xml`、`raw/backend-coverage.json`、`raw/frontend-vitest.json`。
- 配置：`experiment-config.json`、`config/`；环境：`environment.json`。
- 质量报告：`reports/quality-report.md`；测试报告：`reports/testing-report.md`；面试边界：`reports/interview-notes.md`。

## 一键复现

Windows（重跑批准的 live 指标，需要 `DASHSCOPE_API_KEY`，会产生 50 次调用和费用）：

```powershell
powershell -ExecutionPolicy Bypass -File evidence/reproduce.ps1 -IncludeLive
```

仅重建固定数据、规则基线、完整测试和完整性校验：

```powershell
powershell -ExecutionPolicy Bypass -File evidence/reproduce.ps1
```

Linux/macOS：

```bash
DASHSCOPE_API_KEY=... bash evidence/reproduce.sh --include-live
```

live 复现不会使用 `--resume` 或 best-of；同一固定顺序每个 patch 一次。脚本最多只对 transport、408/409/429、5xx 做第二次同输入重试。成本按照实验配置中 2026-07-14 保存的官方示例单价上界估算，实际账单以阿里云控制台为准。

已归档的派生数据和 live 原始结果可在不下载 parquet 时运行 `python scripts/validate_pr_review_evidence.py --require-live --allow-missing-source`；完整 `reproduce` 仍会下载并严格校验上游 SHA。

## 不得扩大表述

- 正例是反向 gold fix，不是自然提交的 buggy PR 分布。
- 控制 patch 只对来源 issue 为负，不是“全局无 bug”。
- 只有一次随机性运行，不能声称均值、置信区间或稳定性。
- Qwen 结果是单 pass 组件，不是完整五 Agent workflow。
- 84% 负例被 flag，不能称为低误报或 production-ready。
- Severity match 40%、category match 36%，不能称为分级/分类准确。
- P50/P95 是当前机器和网络的观察值，不是 SLA。
