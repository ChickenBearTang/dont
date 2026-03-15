#!/usr/bin/env bash
set -euo pipefail

: "${RELEASE_ID:?RELEASE_ID is required}"
: "${GIT_SHA:?GIT_SHA is required}"

RELEASE_DIR="${RELEASE_DIR:-release_out}"
mkdir -p "${RELEASE_DIR}"

shopt -s nullglob
backend_jars=(backend/build/libs/*.jar)
shopt -u nullglob

if [ "${#backend_jars[@]}" -eq 0 ]; then
  echo "[package_release] backend jar not found"
  exit 1
fi

BACKEND_JAR="${backend_jars[0]}"

BACKEND_STAGING="${RELEASE_DIR}/backend-${RELEASE_ID}"
FRONTEND_STAGING="${RELEASE_DIR}/frontend-${RELEASE_ID}"

rm -rf "${BACKEND_STAGING}" "${FRONTEND_STAGING}"
mkdir -p "${BACKEND_STAGING}" "${FRONTEND_STAGING}"

cp "${BACKEND_JAR}" "${BACKEND_STAGING}/app.jar"
cp -R frontend/dist "${FRONTEND_STAGING}/dist"

cat > "${RELEASE_DIR}/manifest-${RELEASE_ID}.json" <<EOF
{
  "releaseId": "${RELEASE_ID}",
  "gitSha": "${GIT_SHA}",
  "components": {
    "backend": "backend-${RELEASE_ID}.tgz",
    "frontend": "frontend-${RELEASE_ID}.tgz"
  }
}
EOF

tar -C "${RELEASE_DIR}" -czf "${RELEASE_DIR}/backend-${RELEASE_ID}.tgz" "backend-${RELEASE_ID}"
tar -C "${RELEASE_DIR}" -czf "${RELEASE_DIR}/frontend-${RELEASE_ID}.tgz" "frontend-${RELEASE_ID}"

echo "[package_release] Artifacts:"
ls -al "${RELEASE_DIR}"
