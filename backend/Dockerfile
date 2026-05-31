ARG USE_CN_MIRROR=0
FROM python:3.12-slim
ARG USE_CN_MIRROR=0

# 国内构建：Debian apt 使用阿里云源
RUN if [ "$USE_CN_MIRROR" = "1" ]; then \
      for f in /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources; do \
        [ -f "$f" ] && sed -i \
          -e 's|deb.debian.org|mirrors.aliyun.com|g' \
          -e 's|security.debian.org|mirrors.aliyun.com|g' \
          "$f" || true; \
      done; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# 国内构建：pip 使用清华源
RUN if [ "$USE_CN_MIRROR" = "1" ]; then \
      pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
      && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn; \
    fi \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
