## Summary
- 详情页三栏审阅布局、demo 验真/索引/变更联动与 rules_only 报告合并（相对 main 的 6 commits）
- 全站中性灰阶毛玻璃与路由/详情 section 转场（Motion + CSS token，无 magic number）
- 修复「导出 Markdown」：Content-Disposition + 程序化下载；export meta 单源；消除静默失败

## 与 llm_mode 关系
导出与下载逻辑对 cloud_only / hybrid / local_only / rules_only 共用，无模式分叉。

## Test plan
- [ ] `cd backend && PYTHONPATH=. pytest tests/ -q`
- [ ] `cd frontend && npm test -- --run && npm run build`
- [ ] Docker：`docker compose build --no-cache frontend && docker compose up -d`，硬刷新 :8080
- [ ] 四种推理模式各完成 1 个任务 → 侧栏「导出 Markdown」本地下载 `.md`
- [ ] 无 result 时按钮禁用或红条提示（非静默、非 JSON 新标签）
- [ ] `prefers-reduced-motion: reduce` 下转场可接受

## 部署说明
- 前端需重建镜像后可见；backend `app` 卷挂载热更新，但建议 `docker compose restart backend` 以加载 export 路由
- 内存任务：backend 重启后旧 taskId 会 404，需重新跑任务验证导出
