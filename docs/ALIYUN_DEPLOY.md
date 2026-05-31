# 阿里云 ECS 线上部署

面向 Ubuntu 22.04 等 Linux VPS（示例公网 IP：`47.96.155.7`）。仓库：[cabbage-pr-review](https://github.com/Yaoniguan-Money/cabbage-pr-review)。

## 选方案

| | 方案 A（无域名） | 方案 B（有域名 + HTTPS） |
|--|------------------|---------------------------|
| 访问 | `http://<公网IP>:8080` | `https://<你的域名>` |
| 命令 | `./scripts/aliyun-setup-demo.sh` | `./scripts/deploy-cloud.sh` |
| 配置 | `.env.demo`（自动） | `.env.production` + `SITE_DOMAIN` |
| 文档 | 本文「方案 A」 | [CLOUD_DEPLOY.md](./CLOUD_DEPLOY.md) |

不确定有没有域名：登录阿里云 **域名** 控制台查看；无域名先用方案 A。

---

## 第 0 步：安全组（阿里云控制台）

路径：**ECS → 实例 → 安全组 → 配置规则 → 入方向**

| 端口 | 协议 | 授权对象 | 用途 |
|------|------|----------|------|
| 22 | TCP | 你的办公 IP 或 `0.0.0.0/0`（演示用） | SSH |
| 8080 | TCP | `0.0.0.0/0` | 方案 A 前端 |
| 80 | TCP | `0.0.0.0/0` | 方案 B HTTP |
| 443 | TCP | `0.0.0.0/0` | 方案 B HTTPS |

保存后，本机 PowerShell 可探测（需已放行）：

```powershell
Test-NetConnection 47.96.155.7 -Port 22
Test-NetConnection 47.96.155.7 -Port 8080
```

服务器上若启用了 `ufw`，还需：

```bash
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp   # 方案 A
sudo ufw allow 80/tcp     # 方案 B
sudo ufw allow 443/tcp    # 方案 B
```

---

## 第 1 步：SSH 登录

```powershell
ssh root@47.96.155.7
# 或创建实例时设置的用户名，如 ubuntu@47.96.155.7
```

首次可用 ECS 控制台 **远程连接** / **重置实例密码**。

---

## 方案 A：一键部署（推荐先跑通）

在服务器上执行（会安装 Docker、克隆仓库、启动服务并做健康检查）：

```bash
curl -fsSL https://raw.githubusercontent.com/Yaoniguan-Money/cabbage-pr-review/main/scripts/aliyun-setup-demo.sh | bash
```

或已 clone 仓库时：

```bash
cd ~/cabbage-pr-review
chmod +x scripts/aliyun-setup-demo.sh scripts/aliyun-verify-demo.sh
./scripts/aliyun-setup-demo.sh
./scripts/aliyun-verify-demo.sh
```

浏览器打开：**http://\<你的公网IP\>:8080**

1. **评委演示 Patch** → 加载 S1 / S2 / S3  
2. 推理模式 **纯规则** → **开始分析**  
3. 详见 [JUDGE_DEMO.md](./JUDGE_DEMO.md)

更新版本：

```bash
cd ~/cabbage-pr-review && git pull && docker compose up --build -d
```

---

## 方案 B：域名 + HTTPS（正式公网）

前提：域名 A 记录已指向 ECS 公网 IP。

```bash
cd ~/cabbage-pr-review
cp .env.production.example .env.production
# 编辑 SITE_DOMAIN=review.你的域名.com
# DEEPSEEK_API_KEY / GITHUB_TOKEN 保持为空
chmod +x scripts/deploy-cloud.sh
./scripts/deploy-cloud.sh
curl -fsS "https://review.你的域名.com/health"
```

评委在浏览器自备 Key，说明见 [CLOUD_DEPLOY.md](./CLOUD_DEPLOY.md)。

从方案 A 切换到 B 时，先停演示栈避免端口冲突：

```bash
cd ~/cabbage-pr-review && docker compose down
./scripts/deploy-cloud.sh
```

---

## 常见问题

1. **外网打不开、SSH 正常** — 几乎总是安全组未放行 8080/80/443。  
2. **build 很慢** — 国内可在 `/etc/docker/daemon.json` 配置阿里云镜像加速。  
3. **方案 B 证书失败** — 域名未解析到本机；先用方案 A。  
4. **日志** — `docker compose logs -f backend` 或 `docker compose -f docker-compose.prod.yml logs -f`。

---

## 脚本索引

| 脚本 | 作用 |
|------|------|
| [scripts/aliyun-setup-demo.sh](../scripts/aliyun-setup-demo.sh) | 安装 Docker + clone + 方案 A 启动 |
| [scripts/aliyun-verify-demo.sh](../scripts/aliyun-verify-demo.sh) | 本机健康检查（8000/8080） |
| [scripts/deploy-cloud.sh](../scripts/deploy-cloud.sh) | 方案 B 生产部署 |
