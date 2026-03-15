#!/usr/bin/env bash
set -euo pipefail

READY_URL="$1"

for _ in $(seq 1 30); do
  if curl -fsS "${READY_URL}" >/dev/null; then
    echo "[verify_local] ready check passed: ${READY_URL}"
    exit 0
  fi
  sleep 2
done

echo "[verify_local] ready check failed: ${READY_URL}"
exit 1
