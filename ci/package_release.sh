#!/usr/bin/env bash
set -euo pipefail

: "${RELEASE_ID:?RELEASE_ID is required}"
: "${GIT_SHA:?GIT_SHA is required}"

RELEASE_DIR="${RELEASE_DIR:-release_out}"
mkdir -p "${RELEASE_DIR}"

shopt -s nullglob
backend_jars=(backend/build/libs/*.jar)
shopt -u nullglob

runtime_jars=()
for jar in "${backend_jars[@]}"; do
  if [[ "${jar}" == *-plain.jar ]]; then
    continue
  fi
  runtime_jars+=("${jar}")
done

if [ "${#runtime_jars[@]}" -eq 0 ]; then
  echo "[package_release] executable backend jar not found"
  exit 1
fi

if [ "${#runtime_jars[@]}" -eq 1 ]; then
  BACKEND_JAR="${runtime_jars[0]}"
else
  preferred_jars=()
  for jar in "${runtime_jars[@]}"; do
    if [[ "${jar}" == *-SNAPSHOT.jar ]]; then
      preferred_jars+=("${jar}")
    fi
  done

  if [ "${#preferred_jars[@]}" -eq 1 ]; then
    BACKEND_JAR="${preferred_jars[0]}"
  else
    echo "[package_release] multiple executable backend jars found: ${runtime_jars[*]}"
    exit 1
  fi
fi

BACKEND_STAGING="${RELEASE_DIR}/backend-${RELEASE_ID}"
FRONTEND_STAGING="${RELEASE_DIR}/frontend-${RELEASE_ID}"
RUNTIME_STAGING="${RELEASE_DIR}/runtime-${RELEASE_ID}"

rm -rf "${BACKEND_STAGING}" "${FRONTEND_STAGING}" "${RUNTIME_STAGING}"
mkdir -p "${BACKEND_STAGING}" "${FRONTEND_STAGING}" "${RUNTIME_STAGING}"

cp "${BACKEND_JAR}" "${BACKEND_STAGING}/app.jar"
cp -R frontend/dist "${FRONTEND_STAGING}/dist"
cp deploy/compose/docker-compose.runtime.yml "${RUNTIME_STAGING}/docker-compose.runtime.yml"
cp deploy/compose/backend.Dockerfile "${RUNTIME_STAGING}/backend.Dockerfile"
cp deploy/compose/frontend.Dockerfile "${RUNTIME_STAGING}/frontend.Dockerfile"

cat > "${RELEASE_DIR}/manifest-${RELEASE_ID}.json" <<EOF
{
  "releaseId": "${RELEASE_ID}",
  "gitSha": "${GIT_SHA}",
  "components": {
    "backend": "backend-${RELEASE_ID}.tgz",
    "frontend": "frontend-${RELEASE_ID}.tgz",
    "runtime": "runtime-${RELEASE_ID}.tgz"
  }
}
EOF

tar -C "${RELEASE_DIR}" -czf "${RELEASE_DIR}/backend-${RELEASE_ID}.tgz" "backend-${RELEASE_ID}"
tar -C "${RELEASE_DIR}" -czf "${RELEASE_DIR}/frontend-${RELEASE_ID}.tgz" "frontend-${RELEASE_ID}"
tar -C "${RELEASE_DIR}" -czf "${RELEASE_DIR}/runtime-${RELEASE_ID}.tgz" "runtime-${RELEASE_ID}"

echo "[package_release] Artifacts:"
ls -al "${RELEASE_DIR}"
