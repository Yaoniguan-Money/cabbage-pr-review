# 本地 Ollama 与混合模式设置

## 安装 Ollama

1. 从 [https://ollama.com](https://ollama.com) 安装 Ollama。
2. 拉取模型（名称自选，示例）：

```powershell
ollama pull qwen2.5:7b
```

## `.env` 配置

```env
LLM_MODE=cloud_only
CLOUD_API_KEY=你的密钥
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_DEFAULT_MODEL=
LOCAL_COMPRESS_ENABLED=true
```

`DEEPSEEK_*` 变量仍可用，会自动映射到 `CLOUD_*`。

## Docker 访问宿主机 Ollama

backend 容器内需访问宿主机 Ollama 时，在 `docker-compose.yml` 为 backend 增加：

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
environment:
  - LOCAL_LLM_BASE_URL=http://host.docker.internal:11434
```

## 验证

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/api/llm-mode-options
```

- `local_available: true` 表示 Ollama 可达。
- 首页选择 **混合** 时，**启用本地输入压缩** 默认勾选；审阅结论仍由云端 Flash/Pro 生成。

## 模式说明

| 模式 | 说明 |
|------|------|
| 纯云端 | 与 v2.1 一致，不依赖 Ollama |
| 混合 | 云端审阅 + 可选本地压缩输入（默认开启压缩） |
| 纯本地 | 全程 Ollama，不要求云端 Key |

详细设计见 [V2.2_LLM_PROVIDER.md](./V2.2_LLM_PROVIDER.md)。

## 质量 KPI 回归（v2.2）

需 Docker + 云端 Key（`cloud_only` / `hybrid`）或本机 Ollama（`local_only` / `hybrid`+压缩）。

```powershell
# 纯云端基线（与 v2.1 一致）
.\scripts\quality_regression.ps1 -PrUrl "https://github.com/owner/repo/pull/N" -LlmMode cloud_only

# 混合 + 本地压缩（对比 Token/降级说明）
.\scripts\quality_regression.ps1 -PrUrl "https://github.com/owner/repo/pull/N" -LlmMode hybrid -LocalCompress $true

# 混合但关闭压缩（应等同 cloud_only 行为）
.\scripts\quality_regression.ps1 -PrUrl "https://github.com/owner/repo/pull/N" -LlmMode hybrid -LocalCompress $false
```

`-LlmMode` 仅传模式 id（`cloud_only` | `hybrid` | `local_only`），阈值仍由脚本参数或 `QUALITY_THRESHOLDS_JSON` 控制。
