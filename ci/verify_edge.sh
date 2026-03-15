#!/usr/bin/env bash
set -euo pipefail

BASE_URL=""
FRONTEND_PATH="/"
HEALTH_PATH="/actuator/health"
AI_SAMPLE_PATH="/api/health/ai"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --frontend-path) FRONTEND_PATH="$2"; shift 2 ;;
    --health-path) HEALTH_PATH="$2"; shift 2 ;;
    --ai-sample-path) AI_SAMPLE_PATH="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [ -z "${BASE_URL}" ]; then
  echo "--base-url is required"
  exit 1
fi

curl -fsSI "${BASE_URL%/}${FRONTEND_PATH}" >/dev/null
curl -fsS "${BASE_URL%/}${HEALTH_PATH}" >/dev/null

if ! curl -fsS "${BASE_URL%/}${AI_SAMPLE_PATH}" >/dev/null; then
  echo "[verify_edge] Warning: AI sample endpoint check failed (${AI_SAMPLE_PATH})"
fi

echo "[verify_edge] Edge checks complete"
