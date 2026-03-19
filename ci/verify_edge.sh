#!/usr/bin/env bash
set -euo pipefail

BASE_URL=""
FRONTEND_PATH="/"
HEALTH_PATH="/actuator/health"
LIVENESS_PATH="/actuator/health/liveness"
READINESS_PATH="/actuator/health/readiness"
AI_SAMPLE_PATH="/api/health/ai"
REQUIRE_AI="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --frontend-path) FRONTEND_PATH="$2"; shift 2 ;;
    --health-path) HEALTH_PATH="$2"; shift 2 ;;
    --liveness-path) LIVENESS_PATH="$2"; shift 2 ;;
    --readiness-path) READINESS_PATH="$2"; shift 2 ;;
    --ai-sample-path) AI_SAMPLE_PATH="$2"; shift 2 ;;
    --require-ai) REQUIRE_AI="true"; shift 1 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [ -z "${BASE_URL}" ]; then
  echo "--base-url is required"
  exit 1
fi

health_status_up() {
  local url="$1"
  local body

  body="$(curl -fsS --retry 5 --retry-delay 2 --max-time 10 "${url}")"
  if ! printf '%s' "${body}" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"UP"'; then
    echo "[verify_edge] health endpoint is not UP: ${url}"
    printf '%s\n' "${body}"
    return 1
  fi
}

curl -fsSI "${BASE_URL%/}${FRONTEND_PATH}" >/dev/null
health_status_up "${BASE_URL%/}${LIVENESS_PATH}"
health_status_up "${BASE_URL%/}${READINESS_PATH}"
health_status_up "${BASE_URL%/}${HEALTH_PATH}"

if ! curl -fsS "${BASE_URL%/}${AI_SAMPLE_PATH}" >/dev/null; then
  if [ "${REQUIRE_AI}" = "true" ]; then
    echo "[verify_edge] AI sample endpoint check failed (${AI_SAMPLE_PATH})"
    exit 1
  fi
  echo "[verify_edge] Warning: AI sample endpoint check failed (${AI_SAMPLE_PATH})"
fi

echo "[verify_edge] Edge checks complete"
