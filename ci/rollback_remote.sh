#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
DEPLOY_ROOT=""
COMPOSE_PROJECT_NAME=""
KNOWN_HOSTS_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    --compose-project-name) COMPOSE_PROJECT_NAME="$2"; shift 2 ;;
    --known-hosts-file) KNOWN_HOSTS_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER DEPLOY_ROOT COMPOSE_PROJECT_NAME KNOWN_HOSTS_FILE; do
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

REMOTE_BASE="${DEPLOY_ROOT%/}"
REMOTE_COMPOSE_FILE="${REMOTE_BASE}/compose/docker-compose.yml"
REMOTE_ENV_FILE="${REMOTE_BASE}/.env"
REMOTE_ENV_PREV_FILE="${REMOTE_BASE}/.env.prev"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "
  set -euo pipefail;
  if [ ! -f '${REMOTE_ENV_PREV_FILE}' ]; then
    echo '[rollback_remote] no previous env snapshot found';
    exit 1;
  fi;
  cp '${REMOTE_ENV_PREV_FILE}' '${REMOTE_ENV_FILE}';
  docker compose \
    --project-name '${COMPOSE_PROJECT_NAME}' \
    --file '${REMOTE_COMPOSE_FILE}' \
    --env-file '${REMOTE_ENV_FILE}' \
    pull;
  docker compose \
    --project-name '${COMPOSE_PROJECT_NAME}' \
    --file '${REMOTE_COMPOSE_FILE}' \
    --env-file '${REMOTE_ENV_FILE}' \
    up -d --remove-orphans;
  docker compose \
    --project-name '${COMPOSE_PROJECT_NAME}' \
    --file '${REMOTE_COMPOSE_FILE}' \
    --env-file '${REMOTE_ENV_FILE}' \
    ps;
"

echo "[rollback_remote] rollback complete on ${HOST}"
