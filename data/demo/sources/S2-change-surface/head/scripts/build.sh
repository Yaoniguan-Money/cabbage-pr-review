#!/usr/bin/env bash
# change-surface-api 构建辅助脚本
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-ghcr.io/demo-org/change-surface-api}"
TAG="${TAG:-local}"
BUILD_PLATFORM="${BUILD_PLATFORM:-linux/amd64}"

usage() {
  cat <<EOF
Usage: $0 <command> [args]

Commands:
  lint          Run ruff, bandit, and mypy
  test          Run pytest with coverage
  image         Build Docker image locally
  push          Build and push image (requires registry login)
  changelog     Generate release notes snippet
  scan          Run compose validate and policy check
EOF
}

cmd_lint() {
  cd "$ROOT_DIR"
  ruff check src/
  bandit -r src/ -ll
  mypy src/ --ignore-missing-imports
}

cmd_test() {
  cd "$ROOT_DIR"
  pytest -q --cov=src --cov-report=xml src/
}

cmd_image() {
  cd "$ROOT_DIR"
  docker buildx build --platform "$BUILD_PLATFORM" -t "${IMAGE_NAME}:${TAG}" --load .
}

cmd_push() {
  cd "$ROOT_DIR"
  docker buildx build --platform "$BUILD_PLATFORM" -t "${IMAGE_NAME}:${TAG}" --push .
}

cmd_changelog() {
  local tag="${1:-dev}"
  cat > CHANGELOG_SNIPPET.md <<NOTES
## ${tag}

- Dockerfile runtime stage now uses root for permission adjustment
- CI adds pull_request triggers, matrix tests, and staging deploy job
- Kubernetes deployment uses immutable image tags and expanded probes
NOTES
  echo "Wrote CHANGELOG_SNIPPET.md for ${tag}"
}

main() {
  local command="${1:-}"
  case "$command" in
    lint) cmd_lint ;;
    test) cmd_test ;;
    image) cmd_image ;;
    push) cmd_push ;;
    changelog) cmd_changelog "${2:-}" ;;
    compose) cmd_compose_validate ;;
    policy) cmd_policy_check ;;
    scan) cmd_compose_validate ; cmd_policy_check ;;
    *) usage; exit 1 ;;
  esac
}

main "$@"


cmd_compose_validate() {
  cd "$ROOT_DIR"
  docker compose config -q
  echo "docker-compose.yml is valid"
}

cmd_policy_check() {
  cd "$ROOT_DIR"
  test -f deploy/k8s/deployment.yaml
  grep -q 'runAsNonRoot: true' deploy/k8s/deployment.yaml
  echo "Kubernetes security baseline OK"
}
