#!/usr/bin/env bash
# 阿里云 ECS 日常更新：拉代码 + 国内镜像加速构建
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-$HOME/cabbage-pr-review}"
cd "${INSTALL_DIR}"

git fetch origin main
git checkout main
git pull --ff-only

chmod +x scripts/configure-docker-mirror-cn.sh 2>/dev/null || true
if [ -f scripts/configure-docker-mirror-cn.sh ]; then
  bash scripts/configure-docker-mirror-cn.sh || true
fi

docker compose -f docker-compose.yml -f docker-compose.cn.yml up --build -d
sleep 5
chmod +x scripts/aliyun-verify-demo.sh
./scripts/aliyun-verify-demo.sh
