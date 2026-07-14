# AI PR Review testing report

## Backend

- 2026-07-14 全量：206 passed，0 failed，0 skipped；JUnit 在 `raw/backend-pytest.xml`。
- Coverage：4491 statements，3814 covered lines，677 missing lines；statement coverage 84.93%，branch coverage 68.53%（1017/1484）；combined display 81%。原始 JSON 在 `raw/backend-coverage.json`。
- 新增 contract 覆盖：rule hit 会携带 unified-diff new-file `line_start/line_end`；多 hunk 行映射有专门测试；RiskItem schema 可传 file/line/category。

Coverage 没有 before 基线，因此不批准为简历“提升”指标，只作为当前工程质量证据。

## Frontend

- Vitest：10 files、35 tests passed；JSON 原始结果在 `raw/frontend-vitest.json`。
- `npm run build` 成功，2777 modules transformed。
- 已知警告：Vite React Babel 的 `esbuild` / `optimizeDeps.esbuildOptions` 已弃用；构建出现两个超过 500 kB 的 chunk（约 615 kB 与 1129 kB）。
- `npm ci` 报告 6 个依赖漏洞（4 moderate、2 high）；没有运行可能破坏兼容性的 `npm audit fix --force`。

## Evidence integrity

`python scripts/validate_pr_review_evidence.py --require-live` fail-closed 校验固定 source/dataset/patch SHA、50 个唯一实例、25/25 标签、五类平衡、rules/live 完整性、混淆矩阵、token 总数、失败 pilot 与批准指标 ID。发布包不提交可下载的上游 parquet；未下载时用 `--allow-missing-source` 校验所有已归档派生数据，完整复现仍严格下载并核验 source SHA。
