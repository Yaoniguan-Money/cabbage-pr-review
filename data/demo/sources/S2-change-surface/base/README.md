# change-surface-api

容器化交付与 CI/CD 流水线示例服务，用于演示 Dockerfile、GitHub Actions 与 Kubernetes 配置变更的审阅场景。

## 架构概览

- **应用**：FastAPI + Uvicorn，暴露 `/health/*` 与 `/metrics`
- **构建**：多阶段 Dockerfile（builder + runtime）
- **CI**：`.github/workflows/ci.yml` 在 `main` 分支 push 时运行 lint / test / build
- **发布**：tag `v*.*.*` 触发 release 工作流并推送 GHCR 镜像
- **部署**：`deploy/k8s/deployment.yaml` 描述双副本 Deployment

## 本地开发

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic-settings httpx prometheus-client pytest
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
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | development | 运行环境 |
| `APP_PORT` | 8080 | 监听端口 |
| `LOG_LEVEL` | info | 日志级别 |
| `METRICS_ENABLED` | true | 是否暴露 Prometheus 指标 |

## 健康检查

- `GET /health/live` — 存活探针
- `GET /health/ready` — 就绪探针，返回环境与指标开关

## 许可证

MIT


## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 容器启动失败 | 端口被占用 | 修改 `APP_PORT` 或 compose 映射 |
| `/health/ready` 404 | 路由未注册 | 确认 `src.main` 已加载 |
| 指标端点空 | `METRICS_ENABLED=false` | 检查环境变量 |

## 发布清单

- [ ] CI lint / test / build 通过
- [ ] 镜像推送到 GHCR
- [ ] 更新 K8s deployment 镜像 tag


## 监控

本地可启用 Prometheus profile：

```bash
docker compose --profile observability up prometheus
```

生产环境通过 ServiceMonitor 抓取 `/metrics`。
