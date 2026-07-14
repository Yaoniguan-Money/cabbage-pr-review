# AI PR Review quality report

运行日期：2026-07-14。数据集：50 个不同的固定 SWE-bench Lite Issue–PR 对，25 positive / 25 control，固定顺序 seed `260714`。所有 case 均保留；没有按结果挑选模型输出或删除难例。

## Patch-level detection

| 模式 | TP | FP | FN | TN | Precision | Recall | F1 | 控制 patch flag rate | 误风险/控制 patch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rules_only | 0 | 1 | 25 | 24 | 0.00% | 0.00% | 0.00% | 4.00% | 0.04 |
| live qwen-plus | 24 | 21 | 1 | 4 | 53.33% | 96.00% | 68.57% | 84.00% | 1.40 |

Qwen 的唯一 FN 是 `prcase-025`（`scikit-learn__scikit-learn-13142`，logic）。21 个控制 patch 被 flag，共产生 35 条控制侧风险。规则基线只在一个控制 patch 误报，未检出任何这组语义缺陷。

## Localization and attributes

分母统一为全部 25 个 positive，而不是只对已检测正例取条件分母：

| 模式 | 文件定位 | 行定位 | 严重级别匹配 | 类别匹配 |
|---|---:|---:|---:|---:|
| rules_only | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) |
| live qwen-plus | 24/25 (96%) | 24/25 (96%) | 10/25 (40%) | 9/25 (36%) |

Qwen 的 patch-level category detection recall：security 5/5、logic 4/5、exception 5/5、compatibility 5/5、performance 5/5。这个值仅表示“是否返回至少一条 risk”，不等同于 risk category 标注准确率；后者按 gold 文件内 category match 只有 36%。

## Latency, tokens, cost

- rules_only P50/P95：20.12/34.80 ms（当前保存的本机离线重跑；延迟会随机器负载变化）。
- qwen-plus P50/P95：3943.06/8989.16 ms。
- Qwen prompt/completion/total：29,466 / 9,900 / 39,366 tokens。
- 估算费用上界：¥0.118332。采用配置中冻结的输入 ¥0.002/1K、输出 ¥0.006/1K 示例价；实际账单以 provider 控制台为准。

## Validity judgment

批准为 **A-qualified**：样本来自真实开源 Issue–PR gold patch、数量达到 50、正负例与五类平衡、规则和 live provider 同场对照、逐 case 原始输出/失败/成本齐全。限定条件是高误报：只写 F1 或 recall 会误导，必须同时报告 precision 或 84% 控制 flag rate。

## Threats to validity

1. 反向 fix 是受控缺陷注入，和自然 buggy PR 的作者、上下文及分布不同。
2. 正向 fix control 只排除其目标 issue 缺陷，不证明无其他可评论风险。
3. Gold 行范围是反向 diff 的所有 changed new-file 行；它是可复现的定位代理，不是人工逐 risk 最小行跨度。
4. 类别由人工选择固定实例，每类 5 个；没有第二标注者一致性统计。
5. 每个 patch 只调用一次；没有跨 seed/temperature 置信区间。
6. 只评估单次结构化 reviewer，不评估仓库上下文获取、Agent 协同、最终报告或人工采纳。
