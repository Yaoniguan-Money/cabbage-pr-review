# Interview notes: what this experiment proves

## 可以回答

- 为什么不用 S1/S2/S3 demo：它们由脚本按已知 rule ID 生成，适合演示回归，不适合无偏质量结论。
- 为什么用 reverse fix：SWE-bench Lite 的 gold patch 提供可追溯真实 OSS 修复；反向后可以稳定重引入来源 issue 缺陷，并从 diff 精确计算 changed new-file 坐标。
- 如何防止泄漏：prompt 只有中性标题和 patch；issue/problem statement、construction、category、severity、gold location 全部不传给 reviewer。
- 如何算定位：路径必须 exact match；行区间必须和该文件精确 changed line 相交；分母为全部 25 个正例。
- 为什么规则 F1=0：默认规则主要捕获词法/治理模式，这组 gold defects 多是语义逻辑；这不是规则引擎普遍无用的结论。
- 为什么 Qwen 仍不是上线结果：recall 96% 但 84% control 被 flag，precision 只有 53.33%；它偏向召回，需要校准、上下文和抑制误报。
- 失败如何处理：DeepSeek 在 14 个成功后余额耗尽，36 个 402；原始结果保留但整轮不批准。当前 harness 已改为永久 HTTP 错误不重试，provider 失败也不再当作 TN/FN。

## 不要声称

- “50 个自然 buggy PR”；正例是反向 gold fix。
- “25 个 clean PR”；它们只是 target-defect-negative controls。
- “多 Agent 系统 F1 68.57%”；只测单 pass reviewer component。
- “严重度/类别准确”；全正例匹配只有 40%/36%。
- “生产低延迟/低成本”；只是一次本机、当前网络、当前 provider 价格快照。
- “结果稳定”；每 patch 只有一次 live 调用。

## 下一轮最有价值改进

1. 增加自然 buggy PR + 人工双人标注与一致性统计，不再只依赖 reverse fixes。
2. 将控制集按“无目标缺陷”和“人工确认无 actionable defect”分层。
3. 在不泄漏 issue 文本的前提下加入最小仓库上下文，优化 precision，并用完全相同 50-case set 做配对比较。
4. 每 patch 至少 3 个固定 seed，报告均值、标准差/置信区间与 provider failure rate。
5. 分别评估 risk-level 精确定位、严重度校准、类别 macro-F1 和人工接受率。
