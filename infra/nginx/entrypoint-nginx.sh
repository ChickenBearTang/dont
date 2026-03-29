#!/bin/sh

set -eu

HTTP_TEMPLATE=/etc/nginx/templates/http.conf
HTTPS_TEMPLATE=/etc/nginx/templates/https.conf
OUTPUT_CONFIG=/etc/nginx/conf.d/default.conf
CERT_FILE=/etc/nginx/certs/fullchain.pem
KEY_FILE=/etc/nginx/certs/privkey.pem

if [ "${SSL_ENABLED:-false}" = "true" ]; then
  if [ ! -s "${CERT_FILE}" ] || [ ! -s "${KEY_FILE}" ]; then
    echo "SSL enabled but certificate files are missing or empty."
    echo "Set SSL_ENABLED=false for HTTP-only mode, or provide valid SSL_CERT_PATH and SSL_KEY_PATH."
    exit 1
  fi
  cp "${HTTPS_TEMPLATE}" "${OUTPUT_CONFIG}"
  echo "TLS enabled for nginx edge: using ${CERT_FILE}, ${KEY_FILE}."
else
  cp "${HTTP_TEMPLATE}" "${OUTPUT_CONFIG}"
  echo "TLS disabled for nginx edge: using HTTP-only config."
fi

exec nginx -g "daemon off;"
