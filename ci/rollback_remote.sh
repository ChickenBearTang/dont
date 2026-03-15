#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
COMPONENT=""
SERVICE=""
DEPLOY_ROOT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --component) COMPONENT="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER COMPONENT SERVICE DEPLOY_ROOT; do
  if [ -z "${!var}" ]; then
    echo "Missing required argument: ${var}"
    exit 1
  fi
done

scp -o StrictHostKeyChecking=accept-new ci/remote/rollback.sh "${USER}@${HOST}:/tmp/rollback.sh"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/rollback.sh '${COMPONENT}' '${SERVICE}' '${DEPLOY_ROOT}'"

echo "[rollback_remote] ${COMPONENT} rollback attempted on ${HOST}"
