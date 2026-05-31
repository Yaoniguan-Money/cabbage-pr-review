# 公网部署（评委自备 API Key）

阿里云 ECS 无域名快速演示见 [ALIYUN_DEPLOY.md](./ALIYUN_DEPLOY.md)（`http://<公网IP>:8080`）。

## 原则

- `DEPLOY_MODE=public`：**不在服务器**写入 `DEEPSEEK_API_KEY` / `CLOUD_API_KEY` / `GITHUB_TOKEN`。
- 首页提供 **《使用说明》**（可折叠）：说明凭据仅存浏览器、评委推荐 Patch+纯规则路径，以及可选的自备 API/Token。
- 评委在「API 与 GitHub 设置」中自备 Key 后可使用云端审阅；不填仍可用 **纯规则** 与 **S1/S2/S3** 演示 Patch。
- `USE_SERVER_GITHUB_TOKEN=false`、`USE_SERVER_CLOUD_CREDENTIALS=false`（`public` 下自动等效）：防止访客任务静默消耗服务器 `.env` 中的个人 Token。

## 步骤

1. 域名 A 记录指向 VPS；安全组放行 **80/443**。
2. `cp .env.production.example .env.production`，编辑 `SITE_DOMAIN=你的域名`。
3. `chmod +x scripts/deploy-cloud.sh && ./scripts/deploy-cloud.sh`
4. 验收：`curl -fsS "https://你的域名/health"`，`llm_enabled` 可为 `false`（正常）。

## 本地开发 vs 公网

| 环境 | `DEPLOY_MODE` | 服务器 Key |
|------|---------------|------------|
| 本地 `.env` | `local`（默认） | 可选，自用 |
| 生产（评委） | `public` | 必须为空；`USE_SERVER_*` 无效 |
| 局域网多人演示 | `public` | 同上，勿用 `local` + 服务器 Token |

## 更新发版

```bash
git pull
./scripts/deploy-cloud.sh
```
