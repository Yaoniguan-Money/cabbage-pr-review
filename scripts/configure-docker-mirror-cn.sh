#!/usr/bin/env bash
# 配置 Docker 守护进程使用国内 registry 镜像加速（拉取 python/node/nginx 等基础镜像）
set -euo pipefail

DAEMON_JSON="/etc/docker/daemon.json"
MIRRORS=(
  "https://docker.m.daocloud.io"
  "https://docker.1ms.run"
  "https://hub-mirror.c.163.com"
)

if ! command -v docker >/dev/null 2>&1; then
  echo "跳过：未安装 Docker"
  exit 0
fi

echo "==> 写入 Docker registry-mirrors（国内加速）..."

python3 - <<'PY' "${DAEMON_JSON}" "${MIRRORS[@]}"
import json
import os
import sys

path = sys.argv[1]
mirrors = sys.argv[2:]

data = {}
if os.path.isfile(path):
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

existing = data.get("registry-mirrors") or []
merged = []
for m in mirrors + existing:
    if m and m not in merged:
        merged.append(m)
data["registry-mirrors"] = merged

os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
print("registry-mirrors:", ", ".join(merged))
PY

if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl restart docker || sudo service docker restart
  echo "==> Docker 已重启"
else
  echo "请手动重启 Docker 使镜像加速生效"
fi
