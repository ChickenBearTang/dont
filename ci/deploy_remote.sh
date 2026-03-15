#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
COMPONENT=""
RELEASE_ID=""
ARCHIVE=""
SERVICE=""
DEPLOY_ROOT=""
READY_URL=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --component) COMPONENT="$2"; shift 2 ;;
    --release-id) RELEASE_ID="$2"; shift 2 ;;
    --archive) ARCHIVE="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    --ready-url) READY_URL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER COMPONENT RELEASE_ID ARCHIVE SERVICE DEPLOY_ROOT READY_URL; do
  if [ -z "${!var}" ]; then
    echo "Missing required argument: ${var}"
    exit 1
  fi
done

if [ ! -f "${ARCHIVE}" ]; then
  echo "Archive not found: ${ARCHIVE}"
  exit 1
fi

REMOTE_TMP="/tmp/${COMPONENT}-${RELEASE_ID}.tgz"

scp -o StrictHostKeyChecking=accept-new "${ARCHIVE}" "${USER}@${HOST}:${REMOTE_TMP}"
scp -o StrictHostKeyChecking=accept-new ci/remote/install_release.sh "${USER}@${HOST}:/tmp/install_release.sh"
scp -o StrictHostKeyChecking=accept-new ci/remote/verify_local.sh "${USER}@${HOST}:/tmp/verify_local.sh"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/install_release.sh '${COMPONENT}' '${RELEASE_ID}' '${REMOTE_TMP}' '${SERVICE}' '${DEPLOY_ROOT}'"

ssh -o StrictHostKeyChecking=accept-new "${USER}@${HOST}" \
  "bash /tmp/verify_local.sh '${READY_URL}'"

echo "[deploy_remote] ${COMPONENT} deployed to ${HOST}"
