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
KNOWN_HOSTS_FILE=""

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
    --known-hosts-file) KNOWN_HOSTS_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER RELEASE_ID BACKEND_ARCHIVE FRONTEND_ARCHIVE RUNTIME_ARCHIVE DEPLOY_ROOT ENV_FILE COMPOSE_PROJECT_NAME BACKEND_READY_URL FRONTEND_READY_URL KNOWN_HOSTS_FILE; do
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

if [ ! -f "${KNOWN_HOSTS_FILE}" ]; then
  echo "Known hosts file not found: ${KNOWN_HOSTS_FILE}"
  exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=yes -o UserKnownHostsFile="${KNOWN_HOSTS_FILE}")

REMOTE_WORKDIR="$(ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "umask 077 && mktemp -d \"\$HOME/deploy-${RELEASE_ID}.XXXXXX\"")"

if [ -z "${REMOTE_WORKDIR}" ]; then
  echo "Failed to allocate remote working directory"
  exit 1
fi

REMOTE_BACKEND_ARCHIVE="${REMOTE_WORKDIR}/backend-${RELEASE_ID}.tgz"
REMOTE_FRONTEND_ARCHIVE="${REMOTE_WORKDIR}/frontend-${RELEASE_ID}.tgz"
REMOTE_RUNTIME_ARCHIVE="${REMOTE_WORKDIR}/runtime-${RELEASE_ID}.tgz"
REMOTE_ENV_FILE="${REMOTE_WORKDIR}/runtime.env"
REMOTE_INSTALL_SCRIPT="${REMOTE_WORKDIR}/install_runtime.sh"
REMOTE_VERIFY_COMPOSE_SCRIPT="${REMOTE_WORKDIR}/verify_compose_health.sh"
REMOTE_VERIFY_LOCAL_SCRIPT="${REMOTE_WORKDIR}/verify_local.sh"

cleanup_remote() {
  ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "rm -rf '${REMOTE_WORKDIR}'" >/dev/null 2>&1 || true
}

trap cleanup_remote EXIT

scp "${SSH_OPTS[@]}" "${BACKEND_ARCHIVE}" "${USER}@${HOST}:${REMOTE_BACKEND_ARCHIVE}"
scp "${SSH_OPTS[@]}" "${FRONTEND_ARCHIVE}" "${USER}@${HOST}:${REMOTE_FRONTEND_ARCHIVE}"
scp "${SSH_OPTS[@]}" "${RUNTIME_ARCHIVE}" "${USER}@${HOST}:${REMOTE_RUNTIME_ARCHIVE}"
scp "${SSH_OPTS[@]}" "${ENV_FILE}" "${USER}@${HOST}:${REMOTE_ENV_FILE}"
scp "${SSH_OPTS[@]}" ci/remote/install_runtime.sh "${USER}@${HOST}:${REMOTE_INSTALL_SCRIPT}"
scp "${SSH_OPTS[@]}" ci/remote/verify_compose_health.sh "${USER}@${HOST}:${REMOTE_VERIFY_COMPOSE_SCRIPT}"
scp "${SSH_OPTS[@]}" ci/remote/verify_local.sh "${USER}@${HOST}:${REMOTE_VERIFY_LOCAL_SCRIPT}"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_INSTALL_SCRIPT}' '${RELEASE_ID}' '${REMOTE_BACKEND_ARCHIVE}' '${REMOTE_FRONTEND_ARCHIVE}' '${REMOTE_RUNTIME_ARCHIVE}' '${DEPLOY_ROOT}' '${REMOTE_ENV_FILE}' '${COMPOSE_PROJECT_NAME}'"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_VERIFY_COMPOSE_SCRIPT}' '${COMPOSE_PROJECT_NAME}' '${DEPLOY_ROOT}/current/runtime/docker-compose.runtime.yml' '${DEPLOY_ROOT}/current/runtime/.env'"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_VERIFY_LOCAL_SCRIPT}' '${BACKEND_READY_URL}'"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_VERIFY_LOCAL_SCRIPT}' '${FRONTEND_READY_URL}'"

trap - EXIT
cleanup_remote

echo "[deploy_runtime_remote] release ${RELEASE_ID} deployed to ${HOST}"
