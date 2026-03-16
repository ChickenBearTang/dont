#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="$1"
COMPOSE_PROJECT_NAME="$2"
LOCK_FILE="${HOME}/.${COMPOSE_PROJECT_NAME}.deploy.lock"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "[rollback_runtime] another deployment operation is in progress"
  exit 1
fi

if ! sudo -n true >/dev/null 2>&1; then
  echo "[rollback_runtime] passwordless sudo is required"
  exit 1
fi

CURRENT_LINK="${DEPLOY_ROOT}/current/runtime"
PREVIOUS_LINK="${DEPLOY_ROOT}/previous/runtime"

if [ ! -L "${PREVIOUS_LINK}" ]; then
  echo "[rollback_runtime] previous runtime link missing"
  exit 1
fi

PREV_TARGET="$(readlink -f "${PREVIOUS_LINK}")"
sudo -n ln -sfn "${PREV_TARGET}" "${CURRENT_LINK}"

if [ ! -f "${CURRENT_LINK}/docker-compose.runtime.yml" ]; then
  echo "[rollback_runtime] compose file missing in rollback target"
  exit 1
fi

if [ ! -f "${CURRENT_LINK}/.env" ]; then
  echo "[rollback_runtime] env file missing in rollback target"
  exit 1
fi

if sudo -n docker compose --help | grep -q -- '--wait'; then
  sudo -n docker compose \
    --project-name "${COMPOSE_PROJECT_NAME}" \
    --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
    --env-file "${CURRENT_LINK}/.env" \
    up -d --remove-orphans --no-build --wait --wait-timeout 120
else
  sudo -n docker compose \
    --project-name "${COMPOSE_PROJECT_NAME}" \
    --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
    --env-file "${CURRENT_LINK}/.env" \
    up -d --remove-orphans --no-build
fi

echo "[rollback_runtime] restored runtime to previous release"
