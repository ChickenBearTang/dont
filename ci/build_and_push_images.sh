#!/usr/bin/env bash
set -euo pipefail

: "${RELEASE_ID:?RELEASE_ID is required}"
: "${GIT_SHA:?GIT_SHA is required}"
: "${DOCKER_REGISTRY:?DOCKER_REGISTRY is required}"
: "${DOCKER_NAMESPACE:?DOCKER_NAMESPACE is required}"
: "${BACKEND_IMAGE_NAME:?BACKEND_IMAGE_NAME is required}"
: "${FRONTEND_IMAGE_NAME:?FRONTEND_IMAGE_NAME is required}"

BACKEND_CONTEXT="release_out/backend-${RELEASE_ID}"
FRONTEND_CONTEXT="release_out/frontend-${RELEASE_ID}"

if [ ! -f "${BACKEND_CONTEXT}/app.jar" ]; then
  echo "[build_and_push_images] missing backend artifact: ${BACKEND_CONTEXT}/app.jar"
  exit 1
fi

if [ ! -d "${FRONTEND_CONTEXT}/dist" ]; then
  echo "[build_and_push_images] missing frontend artifact: ${FRONTEND_CONTEXT}/dist"
  exit 1
fi

BACKEND_IMAGE="${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${BACKEND_IMAGE_NAME}:${GIT_SHA}"
FRONTEND_IMAGE="${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${FRONTEND_IMAGE_NAME}:${GIT_SHA}"

echo "[build_and_push_images] building ${BACKEND_IMAGE}"
docker build \
  -f deploy/compose/backend.Dockerfile \
  -t "${BACKEND_IMAGE}" \
  "${BACKEND_CONTEXT}"

echo "[build_and_push_images] building ${FRONTEND_IMAGE}"
docker build \
  -f deploy/compose/frontend.Dockerfile \
  -t "${FRONTEND_IMAGE}" \
  "${FRONTEND_CONTEXT}"

echo "[build_and_push_images] pushing ${BACKEND_IMAGE}"
docker push "${BACKEND_IMAGE}"

echo "[build_and_push_images] pushing ${FRONTEND_IMAGE}"
docker push "${FRONTEND_IMAGE}"

echo "[build_and_push_images] done"
