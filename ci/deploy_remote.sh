#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER=""
DEPLOY_ROOT=""
COMPOSE_PROJECT_NAME=""
COMPOSE_FILE=""
ENV_FILE=""
KNOWN_HOSTS_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --deploy-root) DEPLOY_ROOT="$2"; shift 2 ;;
    --compose-project-name) COMPOSE_PROJECT_NAME="$2"; shift 2 ;;
    --compose-file) COMPOSE_FILE="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --known-hosts-file) KNOWN_HOSTS_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

for var in HOST USER DEPLOY_ROOT COMPOSE_PROJECT_NAME COMPOSE_FILE ENV_FILE KNOWN_HOSTS_FILE; do
  if [ -z "${!var}" ]; then
    echo "Missing required argument: ${var}"
    exit 1
  fi
done

for file in "${COMPOSE_FILE}" "${ENV_FILE}" "${KNOWN_HOSTS_FILE}"; do
  if [ ! -f "${file}" ]; then
    echo "File not found: ${file}"
    exit 1
  fi
done

if [ ! -f "deploy/nginx/nginx.conf" ] || [ ! -f "deploy/nginx/conf.d/app.conf" ]; then
  echo "Nginx config files are missing under deploy/nginx"
  exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=yes -o UserKnownHostsFile="${KNOWN_HOSTS_FILE}")

REMOTE_BASE="${DEPLOY_ROOT%/}"
REMOTE_COMPOSE_DIR="${REMOTE_BASE}/compose"
REMOTE_NGINX_DIR="${REMOTE_BASE}/nginx"
REMOTE_NGINX_CONF_D_DIR="${REMOTE_NGINX_DIR}/conf.d"
REMOTE_COMPOSE_FILE="${REMOTE_COMPOSE_DIR}/docker-compose.yml"
REMOTE_ENV_FILE="${REMOTE_BASE}/.env"
REMOTE_ENV_PREV_FILE="${REMOTE_BASE}/.env.prev"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
  "mkdir -p '${REMOTE_COMPOSE_DIR}' '${REMOTE_NGINX_CONF_D_DIR}'"

scp "${SSH_OPTS[@]}" "${COMPOSE_FILE}" "${USER}@${HOST}:${REMOTE_COMPOSE_FILE}"
scp "${SSH_OPTS[@]}" deploy/nginx/nginx.conf "${USER}@${HOST}:${REMOTE_NGINX_DIR}/nginx.conf"
scp "${SSH_OPTS[@]}" deploy/nginx/conf.d/app.conf "${USER}@${HOST}:${REMOTE_NGINX_CONF_D_DIR}/app.conf"
scp "${SSH_OPTS[@]}" "${ENV_FILE}" "${USER}@${HOST}:${REMOTE_BASE}/.env.new"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "
  set -euo pipefail;
  if [ -f '${REMOTE_ENV_FILE}' ]; then cp '${REMOTE_ENV_FILE}' '${REMOTE_ENV_PREV_FILE}'; fi;
  mv -f '${REMOTE_BASE}/.env.new' '${REMOTE_ENV_FILE}';
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

echo "[deploy_remote] deployed stack to ${HOST}"
