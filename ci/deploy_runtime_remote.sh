#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
RELEASE_ID=""
BACKEND_ARCHIVE=""
FRONTEND_ARCHIVE=""
RUNTIME_ARCHIVE=""
DEPLOY_ROOT=""
ENV_FILE=""
COMPOSE_PROJECT_NAME=""
BACKEND_READY_URL=""
FRONTEND_READY_URL=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --release-id) RELEASE_ID="$2"; shift 2 ;;
    --backend-archive) BACKEND_ARCHIVE="$2"; shift 2 ;;
    --frontend-archive) FRONTEND_ARCHIVE="$2"; shift 2 ;;
    --runtime-archive) RUNTIME_ARCHIVE="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --compose-project-name) COMPOSE_PROJECT_NAME="$2"; shift 2 ;;
    --backend-ready-url) BACKEND_READY_URL="$2"; shift 2 ;;
    --frontend-ready-url) FRONTEND_READY_URL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER RELEASE_ID BACKEND_ARCHIVE FRONTEND_ARCHIVE RUNTIME_ARCHIVE DEPLOY_ROOT ENV_FILE COMPOSE_PROJECT_NAME BACKEND_READY_URL FRONTEND_READY_URL; do
  if [ -z "${!var}" ]; then
    echo "Missing required argument: ${var}"
    exit 1
  fi
done

for archive in "${BACKEND_ARCHIVE}" "${FRONTEND_ARCHIVE}" "${RUNTIME_ARCHIVE}"; do
  if [ ! -f "${archive}" ]; then
    echo "Archive not found: ${archive}"
    exit 1
  fi
done

if [ ! -f "${ENV_FILE}" ]; then
  echo "Env file not found: ${ENV_FILE}"
  exit 1
fi

REMOTE_BACKEND_ARCHIVE="/tmp/backend-${RELEASE_ID}.tgz"
REMOTE_FRONTEND_ARCHIVE="/tmp/frontend-${RELEASE_ID}.tgz"
REMOTE_RUNTIME_ARCHIVE="/tmp/runtime-${RELEASE_ID}.tgz"
REMOTE_ENV_FILE="$(ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" "umask 077 && mktemp \"\$HOME/runtime-${RELEASE_ID}.XXXXXX.env\"")"

if [ -z "${REMOTE_ENV_FILE}" ]; then
  echo "Failed to allocate remote env temp file"
  exit 1
fi

scp -o StrictHostKeyChecking=accept-new "${BACKEND_ARCHIVE}" "${USER}@${HOST}:${REMOTE_BACKEND_ARCHIVE}"
scp -o StrictHostKeyChecking=accept-new "${FRONTEND_ARCHIVE}" "${USER}@${HOST}:${REMOTE_FRONTEND_ARCHIVE}"
scp -o StrictHostKeyChecking=accept-new "${RUNTIME_ARCHIVE}" "${USER}@${HOST}:${REMOTE_RUNTIME_ARCHIVE}"
scp -p -o StrictHostKeyChecking=accept-new "${ENV_FILE}" "${USER}@${HOST}:${REMOTE_ENV_FILE}"
scp -o StrictHostKeyChecking=accept-new ci/remote/install_runtime.sh "${USER}@${HOST}:/tmp/install_runtime.sh"
scp -o StrictHostKeyChecking=accept-new ci/remote/verify_compose_health.sh "${USER}@${HOST}:/tmp/verify_compose_health.sh"
scp -o StrictHostKeyChecking=accept-new ci/remote/verify_local.sh "${USER}@${HOST}:/tmp/verify_local.sh"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/install_runtime.sh '${RELEASE_ID}' '${REMOTE_BACKEND_ARCHIVE}' '${REMOTE_FRONTEND_ARCHIVE}' '${REMOTE_RUNTIME_ARCHIVE}' '${DEPLOY_ROOT}' '${REMOTE_ENV_FILE}' '${COMPOSE_PROJECT_NAME}'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_compose_health.sh '${COMPOSE_PROJECT_NAME}' '${DEPLOY_ROOT}/current/runtime/docker-compose.runtime.yml' '${DEPLOY_ROOT}/current/runtime/.env'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_local.sh '${BACKEND_READY_URL}'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_local.sh '${FRONTEND_READY_URL}'"

echo "[deploy_runtime_remote] release ${RELEASE_ID} deployed to ${HOST}"
