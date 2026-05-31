#!/usr/bin/env bash
# 方案 A 验收：backend /health 与 frontend 8080
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0

health="$(curl -fsS --max-time 15 http://127.0.0.1:8000/health 2>/dev/null || true)"
if [ -z "${health}" ]; then
  echo "FAIL: backend http://127.0.0.1:8000/health 无响应"
  fail=1
else
  echo "OK: backend /health"
  echo "${health}" | head -c 300
  echo ""
  if echo "${health}" | grep -q '"rules_only"'; then
    echo "OK: llm_mode 含 rules_only（零 Key 演示）"
  else
    echo "WARN: 未在 health 中看到 rules_only，请确认 .env.demo 已加载"
  fi
fi

code="$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://127.0.0.1:8080/ || echo "000")"
if [ "${code}" = "200" ] || [ "${code}" = "304" ]; then
  echo "OK: frontend http://127.0.0.1:8080/ -> HTTP ${code}"
else
  echo "FAIL: frontend HTTP ${code}"
  fail=1
fi

docker compose ps 2>/dev/null || true

if [ "${fail}" -ne 0 ]; then
  echo "查看日志: docker compose logs --tail=50 backend frontend"
  exit 1
fi

echo "验收通过。"
