pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
        ENV_FILE = '.env'
        APP_SERVICES = 'redis backend frontend'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Runtime Config') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'MY_ENV_FILE', variable: 'ENV_SOURCE_FILE')]) {
                        sh '''
                            set -eu
                            install -m 600 "${ENV_SOURCE_FILE}" "${ENV_FILE}"
                        '''
                    }

                    echo "Refreshed ${env.ENV_FILE} from Jenkins credential: MY_ENV_FILE"
                }
            }
        }

        stage('Validate Runtime Config') {
            steps {
                sh '''
                    set -eu
                    set +x

                    test -f "${ENV_FILE}" || {
                      echo "Missing ${ENV_FILE}. Copy .env.example to .env and set RDS/Redis/JWT values."
                      exit 1
                    }

                    get_env_value() {
                      key="$1"
                      awk -F= -v target="$key" '
                        /^[[:space:]]*#/ { next }
                        /^[[:space:]]*$/ { next }
                        {
                          line=$0
                          sub(/\r$/, "", line)
                          pos=index(line, "=")
                          if (pos == 0) next

                          current=substr(line, 1, pos - 1)
                          gsub(/^[[:space:]]+|[[:space:]]+$/, "", current)
                          if (current == target) {
                            print substr(line, pos + 1)
                            found=1
                            exit
                          }
                        }
                        END {
                          if (!found) exit 1
                        }
                      ' "${ENV_FILE}"
                    }

                    strip_outer_quotes() {
                      value="$1"
                      printf '%s' "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
                    }

                    REQUIRED_VARS="DB_URL DB_USERNAME DB_PASSWORD AUTH_JWT_SECRET API_PATH VITE_API_BASE_URL REDIS_HOST REDIS_PORT"
                    for var in ${REQUIRED_VARS}; do
                      value="$(get_env_value "${var}" || true)"
                      value="$(strip_outer_quotes "${value}")"
                      if [ -z "${value}" ]; then
                        echo "Missing required env var: ${var}"
                        exit 1
                      fi
                    done

                    ssl_enabled="$(get_env_value "SSL_ENABLED" || true)"
                    ssl_enabled="$(strip_outer_quotes "${ssl_enabled}")"
                    ssl_enabled="$(printf '%s' "${ssl_enabled}" | tr '[:upper:]' '[:lower:]')"

                    if [ "${ssl_enabled:-false}" = "true" ]; then
                      ssl_cert_path="$(get_env_value "SSL_CERT_PATH" || true)"
                      ssl_key_path="$(get_env_value "SSL_KEY_PATH" || true)"
                      ssl_cert_path="$(strip_outer_quotes "${ssl_cert_path}")"
                      ssl_key_path="$(strip_outer_quotes "${ssl_key_path}")"

                      if [ -z "${ssl_cert_path}" ] || [ -z "${ssl_key_path}" ]; then
                        echo "SSL_ENABLED=true but SSL_CERT_PATH/SSL_KEY_PATH are missing."
                        exit 1
                      fi

                      test -s "${ssl_cert_path}" || {
                        echo "SSL certificate file is not readable or empty: ${ssl_cert_path}"
                        exit 1
                      }

                      test -s "${ssl_key_path}" || {
                        echo "SSL private key file is not readable or empty: ${ssl_key_path}"
                        exit 1
                      }
                    fi
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker version
                    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build --pull
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d ${APP_SERVICES}
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    api_path="$(awk -F= '
                      /^[[:space:]]*#/ { next }
                      /^[[:space:]]*$/ { next }
                      {
                        line=$0
                        sub(/\r$/, "", line)
                        pos=index(line, "=")
                        if (pos == 0) next
                        key=substr(line, 1, pos - 1)
                        gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
                        if (key == "API_PATH") {
                          value=substr(line, pos + 1)
                          gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
                          gsub(/^"|"$/, "", value)
                          gsub(/^'\''|'\''$/, "", value)
                          print value
                          found=1
                          exit
                        }
                      }
                      END {
                        if (!found) print ""
                      }
                    ' "${ENV_FILE}")"

                    if [ -n "${api_path}" ] && [ "${api_path#'/'}" = "${api_path}" ]; then
                      api_path="/${api_path}"
                    fi

                    if [ "${api_path}" != "/" ]; then
                      api_path="${api_path%/}"
                    fi

                    for i in $(seq 1 20); do
                      if docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T frontend \
                           wget -q --spider http://127.0.0.1/ >/dev/null 2>&1; then
                        readiness_ok=0

                        if [ -n "${api_path}" ]; then
                          readiness_body="$(docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T frontend \
                            wget -q -O - "http://backend:8080${api_path}/actuator/health/readiness" || true)"

                          if printf '%s' "${readiness_body}" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"UP"'; then
                            readiness_ok=1
                          fi
                        fi

                        if [ "${readiness_ok}" -ne 1 ]; then
                          readiness_body="$(docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T frontend \
                            wget -q -O - "http://backend:8080/actuator/health/readiness" || true)"

                          if printf '%s' "${readiness_body}" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"UP"'; then
                            readiness_ok=1
                          fi
                        fi

                        if [ "${readiness_ok}" -eq 1 ]; then
                          echo "Smoke test passed"
                          exit 0
                        fi
                      fi

                      sleep 5
                    done

                    echo "Smoke test failed"
                    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            script {
                if (fileExists(env.ENV_FILE)) {
                    sh 'docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps || true'
                } else {
                    echo "Skipping compose ps in post: ${env.ENV_FILE} not found"
                }
            }
        }
        failure {
            script {
                if (fileExists(env.ENV_FILE)) {
                    sh 'docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --tail=100 || true'
                } else {
                    echo "Skipping compose logs in post failure: ${env.ENV_FILE} not found"
                }
            }
        }
    }
}
