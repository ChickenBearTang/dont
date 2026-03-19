#!/usr/bin/env bash
set -euo pipefail

READY_URL="$1"

MAX_ATTEMPTS="${VERIFY_LOCAL_MAX_ATTEMPTS:-60}"
SLEEP_SECONDS="${VERIFY_LOCAL_SLEEP_SECONDS:-2}"
CONNECT_TIMEOUT="${VERIFY_LOCAL_CONNECT_TIMEOUT:-3}"
MAX_TIME="${VERIFY_LOCAL_MAX_TIME:-10}"

for _ in $(seq 1 "${MAX_ATTEMPTS}"); do
  if curl -fsS --connect-timeout "${CONNECT_TIMEOUT}" --max-time "${MAX_TIME}" "${READY_URL}" >/dev/null; then
    echo "[verify_local] ready check passed: ${READY_URL}"
    exit 0
  fi
  sleep "${SLEEP_SECONDS}"
done

echo "[verify_local] ready check failed: ${READY_URL}"
exit 1
