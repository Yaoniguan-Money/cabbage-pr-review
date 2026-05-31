#!/usr/bin/env bash
# 阿里云 ECS 方案 A：安装 Docker、拉代码、docker compose 零 Key 演示
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Yaoniguan-Money/cabbage-pr-review.git}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/cabbage-pr-review}"

echo "==> 检查 Docker..."
if ! command -v docker >/dev/null 2>&1; then
  echo "==> 安装 Docker（get.docker.com）..."
  sudo apt-get update -qq
  sudo apt-get install -y git ca-certificates curl
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  echo "若 docker 命令报权限错误，请退出 SSH 后重新登录，再运行本脚本。"
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "错误: 未找到 docker compose，请确认 Docker 安装完整。"
  exit 1
fi

echo "==> 拉取代码 -> ${INSTALL_DIR}"
if [ -d "${INSTALL_DIR}/.git" ]; then
  git -C "${INSTALL_DIR}" fetch origin main
  git -C "${INSTALL_DIR}" checkout main
  git -C "${INSTALL_DIR}" pull --ff-only
else
  git clone --depth 1 --branch main "${REPO_URL}" "${INSTALL_DIR}"
fi

cd "${INSTALL_DIR}"
echo "==> 启动 docker compose（.env.demo / rules_only）..."
docker compose up --build -d

echo "==> 等待服务就绪..."
sleep 8
chmod +x scripts/aliyun-verify-demo.sh
./scripts/aliyun-verify-demo.sh

PUBLIC_IP="${PUBLIC_IP:-}"
if [ -z "${PUBLIC_IP}" ]; then
  PUBLIC_IP="$(curl -fsS --max-time 3 http://100.100.100.200/latest/meta-data/eip 2>/dev/null || true)"
fi
if [ -n "${PUBLIC_IP}" ]; then
  echo ""
  echo "部署完成。浏览器访问: http://${PUBLIC_IP}:8080"
else
  echo ""
  echo "部署完成。浏览器访问: http://<你的ECS公网IP>:8080"
fi
echo "评委演示: 加载 S1/S2/S3 → 纯规则 → 开始分析"
