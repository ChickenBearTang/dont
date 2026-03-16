#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
DEPLOY_ROOT=""
COMPOSE_PROJECT_NAME=""
BACKEND_READY_URL=""
FRONTEND_READY_URL=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    --compose-project-name) COMPOSE_PROJECT_NAME="$2"; shift 2 ;;
    --backend-ready-url) BACKEND_READY_URL="$2"; shift 2 ;;
    --frontend-ready-url) FRONTEND_READY_URL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER DEPLOY_ROOT COMPOSE_PROJECT_NAME BACKEND_READY_URL FRONTEND_READY_URL; do
  if [ -z "${!var}" ]; then
    echo "Missing required argument: ${var}"
    exit 1
  fi
done

scp -o StrictHostKeyChecking=accept-new ci/remote/rollback_runtime.sh "${USER}@${HOST}:/tmp/rollback_runtime.sh"
scp -o StrictHostKeyChecking=accept-new ci/remote/verify_compose_health.sh "${USER}@${HOST}:/tmp/verify_compose_health.sh"
scp -o StrictHostKeyChecking=accept-new ci/remote/verify_local.sh "${USER}@${HOST}:/tmp/verify_local.sh"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/rollback_runtime.sh '${DEPLOY_ROOT}' '${COMPOSE_PROJECT_NAME}'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_compose_health.sh '${COMPOSE_PROJECT_NAME}' '${DEPLOY_ROOT}/current/runtime/docker-compose.runtime.yml' '${DEPLOY_ROOT}/current/runtime/.env'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_local.sh '${BACKEND_READY_URL}'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_local.sh '${FRONTEND_READY_URL}'"

echo "[rollback_runtime_remote] rollback complete on ${HOST}"
