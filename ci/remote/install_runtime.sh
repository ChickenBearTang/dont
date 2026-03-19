#!/usr/bin/env bash
set -euo pipefail

RELEASE_ID="$1"
BACKEND_ARCHIVE="$2"
FRONTEND_ARCHIVE="$3"
RUNTIME_ARCHIVE="$4"
DEPLOY_ROOT="$5"
RUNTIME_ENV_FILE="$6"
COMPOSE_PROJECT_NAME="$7"
LOCK_FILE="${HOME}/.${COMPOSE_PROJECT_NAME}.deploy.lock"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "[install_runtime] another deployment operation is in progress"
  exit 1
fi

if ! sudo -n true >/dev/null 2>&1; then
  echo "[install_runtime] passwordless sudo is required"
  exit 1
fi

if [ ! -f "${BACKEND_ARCHIVE}" ]; then
  echo "[install_runtime] backend archive not found: ${BACKEND_ARCHIVE}"
  exit 1
fi

if [ ! -f "${FRONTEND_ARCHIVE}" ]; then
  echo "[install_runtime] frontend archive not found: ${FRONTEND_ARCHIVE}"
  exit 1
fi

if [ ! -f "${RUNTIME_ARCHIVE}" ]; then
  echo "[install_runtime] runtime archive not found: ${RUNTIME_ARCHIVE}"
  exit 1
fi

if [ ! -f "${RUNTIME_ENV_FILE}" ]; then
  echo "[install_runtime] runtime env file missing: ${RUNTIME_ENV_FILE}"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[install_runtime] docker command not found"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[install_runtime] docker compose plugin not available"
  exit 1
fi

if ! docker compose --help | grep -q -- '--env-file'; then
  echo "[install_runtime] docker compose does not support --env-file"
  exit 1
fi

RELEASES_DIR="${DEPLOY_ROOT}/releases/runtime"
CURRENT_LINK="${DEPLOY_ROOT}/current/runtime"
PREVIOUS_LINK="${DEPLOY_ROOT}/previous/runtime"
TARGET_DIR="${RELEASES_DIR}/${RELEASE_ID}"

rollback_on_error() {
  rm -f "${RUNTIME_ENV_FILE}" || true

  if [ -L "${PREVIOUS_LINK}" ]; then
    PREV_TARGET="$(readlink -f "${PREVIOUS_LINK}")"
    echo "[install_runtime] deploy failed, attempting rollback to ${PREV_TARGET}"
    sudo -n ln -sfn "${PREV_TARGET}" "${CURRENT_LINK}" || true

    if [ -f "${CURRENT_LINK}/docker-compose.runtime.yml" ] && [ -f "${CURRENT_LINK}/.env" ]; then
      sudo -n docker compose \
        --project-name "${COMPOSE_PROJECT_NAME}" \
        --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
        --env-file "${CURRENT_LINK}/.env" \
        up -d --remove-orphans --no-build || true
    fi
  fi
}

trap rollback_on_error ERR

sudo -n mkdir -p "${RELEASES_DIR}" "$(dirname "${CURRENT_LINK}")" "$(dirname "${PREVIOUS_LINK}")"
sudo -n rm -rf "${TARGET_DIR}"
sudo -n mkdir -p "${TARGET_DIR}/backend" "${TARGET_DIR}/frontend"

sudo -n tar -xzf "${BACKEND_ARCHIVE}" -C "${TARGET_DIR}/backend" --strip-components=1
sudo -n tar -xzf "${FRONTEND_ARCHIVE}" -C "${TARGET_DIR}/frontend" --strip-components=1
sudo -n tar -xzf "${RUNTIME_ARCHIVE}" -C "${TARGET_DIR}" --strip-components=1

if [ ! -f "${TARGET_DIR}/backend/app.jar" ]; then
  echo "[install_runtime] backend app.jar missing after extract"
  exit 1
fi

if [ ! -d "${TARGET_DIR}/frontend/dist" ]; then
  echo "[install_runtime] frontend dist missing after extract"
  exit 1
fi

if [ ! -f "${TARGET_DIR}/docker-compose.runtime.yml" ]; then
  echo "[install_runtime] docker-compose.runtime.yml missing after extract"
  exit 1
fi

sudo -n cp "${TARGET_DIR}/backend.Dockerfile" "${TARGET_DIR}/backend/Dockerfile"
sudo -n cp "${TARGET_DIR}/frontend.Dockerfile" "${TARGET_DIR}/frontend/Dockerfile"

sudo -n cp "${RUNTIME_ENV_FILE}" "${TARGET_DIR}/.env.base"
sudo -n chmod 600 "${TARGET_DIR}/.env.base"
sudo -n bash -c "grep -v '^RELEASE_ID=' '${TARGET_DIR}/.env.base' > '${TARGET_DIR}/.env.new'"
sudo -n bash -c "printf 'RELEASE_ID=%s\n' '${RELEASE_ID}' >> '${TARGET_DIR}/.env.new'"
sudo -n chmod 600 "${TARGET_DIR}/.env.new"
sudo -n mv -f "${TARGET_DIR}/.env.new" "${TARGET_DIR}/.env"
sudo -n rm -f "${TARGET_DIR}/.env.base"
rm -f "${RUNTIME_ENV_FILE}"

if [ -L "${CURRENT_LINK}" ]; then
  PREV_TARGET="$(readlink -f "${CURRENT_LINK}")"
  sudo -n ln -sfn "${PREV_TARGET}" "${PREVIOUS_LINK}"
fi

sudo -n ln -sfn "${TARGET_DIR}" "${CURRENT_LINK}"

if sudo -n docker compose --help | grep -q -- '--wait'; then
  sudo -n docker compose \
    --project-name "${COMPOSE_PROJECT_NAME}" \
    --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
    --env-file "${CURRENT_LINK}/.env" \
    up -d --build --remove-orphans --wait --wait-timeout 120
else
  sudo -n docker compose \
    --project-name "${COMPOSE_PROJECT_NAME}" \
    --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
    --env-file "${CURRENT_LINK}/.env" \
    up -d --build --remove-orphans
fi

trap - ERR

sudo -n docker compose \
  --project-name "${COMPOSE_PROJECT_NAME}" \
  --file "${CURRENT_LINK}/docker-compose.runtime.yml" \
  --env-file "${CURRENT_LINK}/.env" \
  ps

echo "[install_runtime] release=${RELEASE_ID} project=${COMPOSE_PROJECT_NAME}"
