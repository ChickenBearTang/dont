#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="$1"
COMPOSE_PROJECT_NAME="$2"

CURRENT_LINK="${DEPLOY_ROOT}/current/runtime"
PREVIOUS_LINK="${DEPLOY_ROOT}/previous/runtime"

if [ ! -L "${PREVIOUS_LINK}" ]; then
  echo "[rollback_runtime] previous runtime link missing"
  exit 1
fi

PREV_TARGET="$(readlink -f "${PREVIOUS_LINK}")"
sudo ln -sfn "${PREV_TARGET}" "${CURRENT_LINK}"

if [ ! -f "${CURRENT_LINK}/docker-compose.runtime.yml" ]; then
  echo "[rollback_runtime] compose file missing in rollback target"
  exit 1
fi

if [ ! -f "${CURRENT_LINK}/.env" ]; then
  echo "[rollback_runtime] env file missing in rollback target"
  exit 1
fi

if sudo docker compose --help | grep -q -- '--wait'; then
  sudo docker compose \
    --project-name "${COMPOSE_PROJECT_NAME}" \
    --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
    --env-file "${CURRENT_LINK}/.env" \
    up -d --build --remove-orphans --wait --wait-timeout 120
else
  sudo docker compose \
    --project-name "${COMPOSE_PROJECT_NAME}" \
    --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
    --env-file "${CURRENT_LINK}/.env" \
    up -d --build --remove-orphans
fi

echo "[rollback_runtime] restored runtime to previous release"
