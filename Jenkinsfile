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
        APP_SERVICES = 'redis backend frontend edge-nginx'
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
                    if (!fileExists(env.ENV_FILE)) {
                        withCredentials([file(credentialsId: 'MY_ENV_FILE', variable: 'ENV_SOURCE_FILE')]) {
                            sh '''
                                set -eu
                                install -m 600 "${ENV_SOURCE_FILE}" "${ENV_FILE}"
                            '''
                        }

                        echo "Created ${env.ENV_FILE} from Jenkins credential: MY_ENV_FILE"
                    }
                }
            }
        }

        stage('Validate Runtime Config') {
            steps {
                sh '''
                    set -eu

                    test -f "${ENV_FILE}" || {
                      echo "Missing ${ENV_FILE}. Copy .env.example to .env and set RDS/Redis/JWT values."
                      exit 1
                    }

                    set -a
                    . "./${ENV_FILE}"
                    set +a

                    REQUIRED_VARS="DB_URL DB_USERNAME DB_PASSWORD AUTH_JWT_SECRET API_PATH VITE_API_BASE_URL REDIS_HOST REDIS_PORT"
                    for var in ${REQUIRED_VARS}; do
                      eval "value=\"\${$var-}\""
                      if [ -z "$value" ]; then
                        echo "Missing required env var: ${var}"
                        exit 1
                      fi
                    done

                    if [ "${SSL_ENABLED:-false}" = "true" ]; then
                      if [ -z "${SSL_CERT_PATH-}" ] || [ -z "${SSL_KEY_PATH-}" ]; then
                        echo "SSL_ENABLED=true but SSL_CERT_PATH/SSL_KEY_PATH are missing."
                        exit 1
                      fi
                      test -s "${SSL_CERT_PATH}" || {
                        echo "SSL certificate file is not readable or empty: ${SSL_CERT_PATH}"
                        exit 1
                      }
                      test -s "${SSL_KEY_PATH}" || {
                        echo "SSL private key file is not readable or empty: ${SSL_KEY_PATH}"
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
                    for i in $(seq 1 20); do
                      if curl -fsS http://127.0.0.1/ >/dev/null && \
                         curl -fsS http://127.0.0.1/api/v1/actuator/health/readiness >/dev/null; then
                        echo "Smoke test passed"
                        exit 0
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
