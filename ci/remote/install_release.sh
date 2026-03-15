#!/usr/bin/env bash
set -euo pipefail

COMPONENT="$1"
RELEASE_ID="$2"
ARCHIVE_PATH="$3"
SERVICE_NAME="$4"
DEPLOY_ROOT="$5"

RELEASES_DIR="${DEPLOY_ROOT}/releases/${COMPONENT}"
CURRENT_LINK="${DEPLOY_ROOT}/current/${COMPONENT}"
PREVIOUS_LINK="${DEPLOY_ROOT}/previous/${COMPONENT}"
TARGET_DIR="${RELEASES_DIR}/${RELEASE_ID}"

sudo mkdir -p "${RELEASES_DIR}" "$(dirname "${CURRENT_LINK}")" "$(dirname "${PREVIOUS_LINK}")"
sudo rm -rf "${TARGET_DIR}"
sudo mkdir -p "${TARGET_DIR}"

sudo tar -xzf "${ARCHIVE_PATH}" -C "${TARGET_DIR}" --strip-components=1

if [ -L "${CURRENT_LINK}" ]; then
  PREV_TARGET="$(readlink -f "${CURRENT_LINK}")"
  sudo ln -sfn "${PREV_TARGET}" "${PREVIOUS_LINK}"
fi

sudo ln -sfn "${TARGET_DIR}" "${CURRENT_LINK}"
sudo systemctl restart "${SERVICE_NAME}"
sudo systemctl status "${SERVICE_NAME}" --no-pager

echo "[install_release] component=${COMPONENT} release=${RELEASE_ID} service=${SERVICE_NAME}"
