#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
DEPLOY_ROOT=""
COMPOSE_PROJECT_NAME=""
BACKEND_READY_URL=""
FRONTEND_READY_URL=""
KNOWN_HOSTS_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    --compose-project-name) COMPOSE_PROJECT_NAME="$2"; shift 2 ;;
    --backend-ready-url) BACKEND_READY_URL="$2"; shift 2 ;;
    --frontend-ready-url) FRONTEND_READY_URL="$2"; shift 2 ;;
    --known-hosts-file) KNOWN_HOSTS_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER DEPLOY_ROOT COMPOSE_PROJECT_NAME BACKEND_READY_URL FRONTEND_READY_URL KNOWN_HOSTS_FILE; do
  if [ -z "${!var}" ]; then
    echo "Missing required argument: ${var}"
    exit 1
  fi
done

if [ ! -f "${KNOWN_HOSTS_FILE}" ]; then
  echo "Known hosts file not found: ${KNOWN_HOSTS_FILE}"
  exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=yes -o UserKnownHostsFile="${KNOWN_HOSTS_FILE}")

REMOTE_WORKDIR="$(ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "umask 077 && mktemp -d \"\$HOME/rollback-${COMPOSE_PROJECT_NAME}.XXXXXX\"")"

if [ -z "${REMOTE_WORKDIR}" ]; then
  echo "Failed to allocate remote rollback working directory"
  exit 1
fi

REMOTE_ROLLBACK_SCRIPT="${REMOTE_WORKDIR}/rollback_runtime.sh"
REMOTE_VERIFY_COMPOSE_SCRIPT="${REMOTE_WORKDIR}/verify_compose_health.sh"
REMOTE_VERIFY_LOCAL_SCRIPT="${REMOTE_WORKDIR}/verify_local.sh"

cleanup_remote() {
  ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "rm -rf '${REMOTE_WORKDIR}'" >/dev/null 2>&1 || true
}

trap cleanup_remote EXIT

scp "${SSH_OPTS[@]}" ci/remote/rollback_runtime.sh "${USER}@${HOST}:${REMOTE_ROLLBACK_SCRIPT}"
scp "${SSH_OPTS[@]}" ci/remote/verify_compose_health.sh "${USER}@${HOST}:${REMOTE_VERIFY_COMPOSE_SCRIPT}"
scp "${SSH_OPTS[@]}" ci/remote/verify_local.sh "${USER}@${HOST}:${REMOTE_VERIFY_LOCAL_SCRIPT}"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_ROLLBACK_SCRIPT}' '${DEPLOY_ROOT}' '${COMPOSE_PROJECT_NAME}'"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_VERIFY_COMPOSE_SCRIPT}' '${COMPOSE_PROJECT_NAME}' '${DEPLOY_ROOT}/current/runtime/docker-compose.runtime.yml' '${DEPLOY_ROOT}/current/runtime/.env'"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_VERIFY_LOCAL_SCRIPT}' '${BACKEND_READY_URL}'"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "bash '${REMOTE_VERIFY_LOCAL_SCRIPT}' '${FRONTEND_READY_URL}'"

trap - EXIT
cleanup_remote

echo "[rollback_runtime_remote] rollback complete on ${HOST}"
