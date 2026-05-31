# 零 API Key 演示：等同于仓库根目录 docker compose up --build
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
docker compose up --build @args
