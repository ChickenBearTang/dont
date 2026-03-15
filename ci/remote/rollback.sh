#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
SERVICE_NAME="$2"
DEPLOY_ROOT="$3"

CURRENT_LINK="${DEPLOY_ROOT}/current/${COMPONENT}"
PREVIOUS_LINK="${DEPLOY_ROOT}/previous/${COMPONENT}"

if [ ! -L "${PREVIOUS_LINK}" ]; then
  echo "[rollback] previous link missing for component=${COMPONENT}"
  exit 1
fi

PREV_TARGET="$(readlink -f "${PREVIOUS_LINK}")"
sudo ln -sfn "${PREV_TARGET}" "${CURRENT_LINK}"
sudo systemctl restart "${SERVICE_NAME}"
sudo systemctl status "${SERVICE_NAME}" --no-pager

echo "[rollback] component=${COMPONENT} restored to previous target"
