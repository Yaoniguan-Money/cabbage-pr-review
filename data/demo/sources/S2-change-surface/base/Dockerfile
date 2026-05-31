# syntax=docker/dockerfile:1.6
# change-surface-api — 多阶段构建，生产镜像以非 root 用户运行

ARG PYTHON_VERSION=3.12
ARG BUILDKIT_INLINE_CACHE=1

FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

COPY pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel \
    && pip wheel --wheel-dir /wheels \
        "fastapi>=0.110" \
        "uvicorn[standard]>=0.27" \
        "pydantic-settings>=2.2" \
        "httpx>=0.27" \
        "prometheus-client>=0.20"

FROM base AS runtime

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels fastapi uvicorn pydantic-settings httpx prometheus-client \
    && rm -rf /wheels

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY deploy/ ./deploy/

RUN groupadd -r appgroup && useradd -r -g appgroup -d ${APP_HOME} -s /sbin/nologin appuser \
    && chown -R appuser:appgroup ${APP_HOME} \
    && chmod +x ${APP_HOME}/scripts/build.sh

USER appuser

EXPOSE 8080

ENV APP_ENV=production \
    APP_PORT=8080 \
    APP_BIND=0.0.0.0 \
    LOG_LEVEL=info \
    METRICS_ENABLED=true \
    REQUEST_TIMEOUT_SECONDS=30

LABEL org.opencontainers.image.title="change-surface-api" \
      org.opencontainers.image.description="Demo API for container delivery and CI/CD change review" \
      org.opencontainers.image.vendor="demo-org" \
      org.opencontainers.image.source="https://github.com/demo-org/change-surface-api" \
      org.opencontainers.image.licenses="MIT"

# 构建元数据（供 SBOM 与镜像溯源使用）
LABEL build.python.version="${PYTHON_VERSION}" \
      build.pipeline="github-actions" \
      build.target="production"

# 运行时观测与运维约定
ENV OTEL_SERVICE_NAME=change-surface-api \
    OTEL_EXPORTER_OTLP_ENDPOINT="" \
    OTEL_TRACES_SAMPLER=parentbased_traceidratio \
    OTEL_TRACES_SAMPLER_ARG=0.1

# 进程与信号处理
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${APP_PORT}/health/live || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# 生产镜像为默认 target；本地调试请使用 docker compose
