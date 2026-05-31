# change-surface-api

容器化交付与 CI/CD 流水线示例服务，用于演示 Dockerfile、GitHub Actions 与 Kubernetes 配置变更的审阅场景。

## 架构概览

- **应用**：FastAPI + Uvicorn，暴露 `/health/*`、`/metrics` 与 `/api/v1/deploy`
- **构建**：多阶段 Dockerfile（builder + runtime），runtime 阶段含 root 权限调整步骤
- **CI**：`.github/workflows/ci.yml` 支持 `main` push 与 pull request，含 staging 部署 job
- **发布**：tag 或手动 dispatch 触发 release，镜像签名（cosign）与 SBOM
- **部署**：`deploy/k8s/deployment.yaml` 三副本 Deployment，镜像 tag 由 CI 注入

## 本地开发

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic-settings httpx prometheus-client pytest bandit ruff
python -m src.main
```

或使用 Docker Compose：

```bash
docker compose up --build
```

## 构建脚本

```bash
./scripts/build.sh lint
./scripts/build.sh test
./scripts/build.sh image
./scripts/build.sh push   # 需要已登录 registry
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | development | 运行环境 |
| `APP_PORT` | 8080 | 监听端口 |
| `LOG_LEVEL` | info | 日志级别 |
| `METRICS_ENABLED` | true | 是否暴露 Prometheus 指标 |
| `REQUEST_TIMEOUT_SECONDS` | 45 | HTTP keep-alive 超时 |
| `DEPLOY_REGION` | us-east-1 | 部署区域标识 |
| `FEATURE_CANARY` | false | 金丝雀功能开关 |

## 健康检查

- `GET /health/live` — 存活探针
- `GET /health/ready` — 就绪探针，返回环境、指标开关与超时配置
- `GET /api/v1/deploy` — 部署元数据（pipeline、镜像坐标）

## CI/CD 变更说明

1. Dockerfile 在 runtime 阶段新增 `USER root` 以调整脚本权限（审阅时请评估特权风险）
2. CI 增加 PR 触发、Python 矩阵测试、GHCR 推送与 staging 部署
3. Kubernetes 清单改为可变镜像 tag，并挂载 Secret

## 许可证

MIT


## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 容器启动失败 | 端口被占用或 root 权限步骤失败 | 检查 Dockerfile runtime 阶段日志 |
| `/health/ready` 超时 | `REQUEST_TIMEOUT_SECONDS` 过小 | 在 ConfigMap 中调高超时 |
| 指标端点空 | `METRICS_ENABLED=false` | 检查环境变量 |
| staging 部署失败 | `KUBE_CONFIG_STAGING` 过期 | 轮换密钥并重跑 deploy job |

## 发布清单

- [ ] CI lint / test / build / deploy 通过
- [ ] Trivy 扫描无 HIGH 漏洞
- [ ] 镜像推送到 GHCR 且 cosign 签名完成
- [ ] 更新 K8s deployment 镜像 tag 与 Secret 引用
- [ ] post-release smoke 访问 staging 成功

## 安全审阅要点

1. Dockerfile 中 `USER root` 仅应用于 chmod，最终仍回落到 `appuser`
2. CI 新增 `id-token: write` 用于 OIDC 登录 GHCR
3. deploy job 使用 `secrets.KUBE_CONFIG_STAGING`，需确认最小权限


## 监控

本地可启用完整 observability profile：

```bash
docker compose --profile observability --profile cache up
```

生产环境通过 ServiceMonitor 抓取 `/metrics`，并将 trace 导出至 OTLP Collector。
金丝雀发布期间请对比 `deploy_info_requests_total` 与错误率。
