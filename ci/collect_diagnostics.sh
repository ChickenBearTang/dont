#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="release_out/diagnostics"
mkdir -p "${OUT_DIR}"

SSH_OPTS=(-o StrictHostKeyChecking=yes)
if [ -n "${SSH_KNOWN_HOSTS_FILE:-}" ]; then
  SSH_OPTS+=(-o UserKnownHostsFile="${SSH_KNOWN_HOSTS_FILE}")
fi

{
  echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "branch=${BRANCH_NAME:-unknown}"
  echo "release_id=${RELEASE_ID:-unknown}"
} > "${OUT_DIR}/pipeline-context.txt"

if [ -n "${MAIN_SERVER_HOST:-}" ] && [ -n "${MAIN_SERVER_USER:-}" ]; then
  ssh "${SSH_OPTS[@]}" "${MAIN_SERVER_USER}@${MAIN_SERVER_HOST}" \
    "hostname && date && \
    if ! command -v docker >/dev/null 2>&1; then \
      echo 'docker command not found on main server'; \
      exit 1; \
    fi && \
    if [ ! -f '${MAIN_DEPLOY_ROOT:-/opt/awesome-spring-project}/current/runtime/docker-compose.runtime.yml' ]; then \
      echo 'runtime compose file missing on main server'; \
      exit 1; \
    fi && \
    if [ ! -f '${MAIN_DEPLOY_ROOT:-/opt/awesome-spring-project}/current/runtime/.env' ]; then \
      echo 'runtime .env missing on main server'; \
      exit 1; \
    fi && \
    sudo docker compose --project-name ${COMPOSE_PROJECT_NAME:-awesome-runtime} --file '${MAIN_DEPLOY_ROOT:-/opt/awesome-spring-project}/current/runtime/docker-compose.runtime.yml' --env-file '${MAIN_DEPLOY_ROOT:-/opt/awesome-spring-project}/current/runtime/.env' ps && \
    sudo docker compose --project-name ${COMPOSE_PROJECT_NAME:-awesome-runtime} --file '${MAIN_DEPLOY_ROOT:-/opt/awesome-spring-project}/current/runtime/docker-compose.runtime.yml' --env-file '${MAIN_DEPLOY_ROOT:-/opt/awesome-spring-project}/current/runtime/.env' logs --tail=200" \
    > "${OUT_DIR}/main-server-status.txt" 2>&1 || true
fi

if [ -n "${AI_SERVER_HOST:-}" ] && [ -n "${AI_SERVER_USER:-}" ]; then
  ssh "${SSH_OPTS[@]}" "${AI_SERVER_USER}@${AI_SERVER_HOST}" \
    "hostname && date" \
    > "${OUT_DIR}/ai-server-status.txt" 2>&1 || true
fi

echo "[collect_diagnostics] Wrote diagnostics to ${OUT_DIR}"
