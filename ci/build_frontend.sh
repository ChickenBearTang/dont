#!/usr/bin/env bash
set -euo pipefail

echo "[build_frontend] Installing dependencies"
npm --prefix frontend ci

if [ "${INFRA_SMOKE_MODE:-false}" != "true" ] && [ "${CI_SKIP_FRONTEND_LINT:-false}" != "true" ]; then
  echo "[build_frontend] Running lint"
  npm --prefix frontend run lint
fi

echo "[build_frontend] Building frontend"
npm --prefix frontend run build

echo "[build_frontend] Done"
