#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROJECT_NAME="$1"
COMPOSE_FILE="$2"
ENV_FILE="$3"

if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "[verify_compose_health] compose file missing: ${COMPOSE_FILE}"
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  echo "[verify_compose_health] env file missing: ${ENV_FILE}"
  exit 1
fi

for _ in $(seq 1 30); do
  container_ids="$(sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps -q)"

  if [ -z "${container_ids}" ]; then
    sleep 2
    continue
  fi

  unhealthy=0
  for container_id in ${container_ids}; do
    status="$(sudo docker inspect -f '{{.State.Status}}' "${container_id}")"
    if [ "${status}" != "running" ]; then
      unhealthy=1
      break
    fi

    health_status="$(sudo docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "${container_id}")"
    if [ -z "${health_status}" ]; then
      unhealthy=1
      break
    fi

    if [ "${health_status}" != "healthy" ]; then
      unhealthy=1
      break
    fi
  done

  if [ "${unhealthy}" -eq 0 ]; then
    echo "[verify_compose_health] all containers are running and healthy"
    exit 0
  fi

  sleep 2
done

echo "[verify_compose_health] timed out waiting for healthy compose services"
sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps || true
sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --tail=200 || true
exit 1
