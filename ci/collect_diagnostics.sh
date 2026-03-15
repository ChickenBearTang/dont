#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="release_out/diagnostics"
mkdir -p "${OUT_DIR}"

{
  echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "branch=${BRANCH_NAME:-unknown}"
  echo "release_id=${RELEASE_ID:-unknown}"
} > "${OUT_DIR}/pipeline-context.txt"

if [ -n "${MAIN_SERVER_HOST:-}" ] && [ -n "${MAIN_SERVER_USER:-}" ]; then
  ssh -o StrictHostKeyChecking=accept-new "${MAIN_SERVER_USER}@${MAIN_SERVER_HOST}" \
    "hostname && date && systemctl status ${BACKEND_SERVICE_NAME:-spring-backend} --no-pager && systemctl status ${FRONTEND_SERVICE_NAME:-frontend-node} --no-pager" \
    > "${OUT_DIR}/main-server-status.txt" 2>&1 || true
fi

if [ -n "${AI_SERVER_HOST:-}" ] && [ -n "${AI_SERVER_USER:-}" ]; then
  ssh -o StrictHostKeyChecking=accept-new "${AI_SERVER_USER}@${AI_SERVER_HOST}" \
    "hostname && date" \
    > "${OUT_DIR}/ai-server-status.txt" 2>&1 || true
fi

echo "[collect_diagnostics] Wrote diagnostics to ${OUT_DIR}"
