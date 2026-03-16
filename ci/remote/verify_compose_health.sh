#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROJECT_NAME="$1"
COMPOSE_FILE="$2"
ENV_FILE="$3"
MAX_ATTEMPTS="${VERIFY_COMPOSE_MAX_ATTEMPTS:-90}"
SLEEP_SECONDS="${VERIFY_COMPOSE_SLEEP_SECONDS:-2}"

if ! sudo -n true >/dev/null 2>&1; then
  echo "[verify_compose_health] passwordless sudo is required"
  exit 1
fi

if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "[verify_compose_health] compose file missing: ${COMPOSE_FILE}"
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  echo "[verify_compose_health] env file missing: ${ENV_FILE}"
  exit 1
fi

for _ in $(seq 1 "${MAX_ATTEMPTS}"); do
  container_ids="$(sudo -n docker compose --project-name "${COMPOSE_PROJECT_NAME}" --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q)"

  if [ -z "${container_ids}" ]; then
    sleep 2
    continue
  fi

  unhealthy=0
  for container_id in ${container_ids}; do
    status="$(sudo -n docker inspect -f '{{.State.Status}}' "${container_id}")"
    if [ "${status}" != "running" ]; then
      unhealthy=1
      break
    fi

    health_status="$(sudo -n docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "${container_id}")"
    if [ -n "${health_status}" ] && [ "${health_status}" != "healthy" ]; then
      unhealthy=1
      break
    fi
  done

  if [ "${unhealthy}" -eq 0 ]; then
    echo "[verify_compose_health] all containers are running and healthy"
    exit 0
  fi

  sleep "${SLEEP_SECONDS}"
done

echo "[verify_compose_health] timed out waiting for healthy compose services"
sudo -n docker compose --project-name "${COMPOSE_PROJECT_NAME}" --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps || true
sudo -n docker compose --project-name "${COMPOSE_PROJECT_NAME}" --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --tail=200 || true
exit 1
