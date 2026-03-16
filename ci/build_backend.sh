#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[build_backend] Building backend"
if [ "${INFRA_SMOKE_MODE:-false}" = "true" ] || [ "${CI_SKIP_BACKEND_TESTS:-false}" = "true" ]; then
  bash "${REPO_ROOT}/backend/gradlew" -p "${REPO_ROOT}/backend" clean build -x test -x spotlessCheck -x spotlessJavaCheck
else
  bash "${REPO_ROOT}/backend/gradlew" -p "${REPO_ROOT}/backend" clean test build
fi

echo "[build_backend] Done"
