#!/usr/bin/env bash
# change-surface-api 构建辅助脚本
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-ghcr.io/demo-org/change-surface-api}"
TAG="${TAG:-local}"

usage() {
  cat <<EOF
Usage: $0 <command> [args]

Commands:
  lint          Run ruff and mypy
  test          Run pytest
  image         Build Docker image locally
  changelog     Generate release notes snippet
EOF
}

cmd_lint() {
  cd "$ROOT_DIR"
  ruff check src/
  mypy src/ --ignore-missing-imports
}

cmd_test() {
  cd "$ROOT_DIR"
  pytest -q src/
}

cmd_image() {
  cd "$ROOT_DIR"
  docker build -t "${IMAGE_NAME}:${TAG}" .
}

cmd_changelog() {
  local tag="${1:-dev}"
  cat > CHANGELOG_SNIPPET.md <<NOTES
## ${tag}

- Container image rebuilt with multi-stage Dockerfile
- CI pipeline validates lint, test, and image build
NOTES
  echo "Wrote CHANGELOG_SNIPPET.md for ${tag}"
}

main() {
  local command="${1:-}"
  case "$command" in
    lint) cmd_lint ;;
    test) cmd_test ;;
    image) cmd_image ;;
    changelog) cmd_changelog "${2:-}" ;;
    compose) cmd_compose_validate ;;
    *) usage; exit 1 ;;
  esac
}

main "$@"


cmd_compose_validate() {
  cd "$ROOT_DIR"
  docker compose config -q
}
