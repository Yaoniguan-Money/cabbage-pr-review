#!/usr/bin/env bash
# 云服务器生产部署（不在服务器写入 API Key）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STRICT=0
for arg in "$@"; do
  if [ "$arg" = "--strict" ]; then
    STRICT=1
  fi
done

if [ ! -f .env.production ]; then
  cp .env.production.example .env.production
  echo "已创建 .env.production，请设置 SITE_DOMAIN 后重新运行。"
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env.production
set +a

for var in DEEPSEEK_API_KEY CLOUD_API_KEY GITHUB_TOKEN; do
  val="${!var:-}"
  if [ -n "$val" ]; then
    echo "警告: $var 在生产环境中非空（public 模式将忽略云端/GitHub 服务器 Key）"
    if [ "$STRICT" -eq 1 ]; then
      echo "严格模式：请清空 $var 后重试"
      exit 1
    fi
  fi
done

export SITE_DOMAIN="${SITE_DOMAIN:-localhost}"

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

echo "部署完成。请访问 https://${SITE_DOMAIN}/ （本地测试可用 http://localhost:8080 若仅映射 frontend）"
echo "评委在首页「API 与 GitHub 设置」中自备 Key 后选择纯云端。"
