# Docker + Jenkins Quick Infra Setup

This setup keeps infra simple while using the required stack:

- `nginx` (edge reverse proxy)
- `springboot` (backend)
- `react` (frontend static build)
- `redis`
- external `RDS` (configured through `.env`)
- `jenkins` (optional profile)

## 1) Prepare env

```bash
cp .env.example .env
```

Edit `.env` values, especially:

- `DB_URL`, `DB_USERNAME`, `DB_PASSWORD` (external RDS)
- `AUTH_JWT_SECRET`
- `VITE_API_BASE_URL` (`/api/v1` recommended)
- `SSL_ENABLED` (`false` for HTTP-only, `true` for TLS)
- `SSL_CERT_PATH`, `SSL_KEY_PATH` (host absolute path, required only when SSL_ENABLED=true)

Example:

```bash
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/example.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/example.com/privkey.pem
```

Note:

- Keep `API_PATH=/api/v1` and `VITE_API_BASE_URL=/api/v1` aligned.
- `REDIS_HOST=localhost` in `.env.example` is fine for local non-container usage, and `docker-compose` overrides backend container runtime to use `redis` internally.
- `SSL_ENABLED=true` enables HTTPS listener on `443`; set to `false` while developing without certs.

## 2) Run application stack

```bash
docker compose up -d --build redis backend frontend edge-nginx
```

Access:

- App entry: `http://localhost`
- HTTPS entry: `https://localhost` (certificate must match your domain, only when SSL_ENABLED=true)
- Backend readiness: `http://localhost/api/v1/actuator/health/readiness`

## 3) Run Jenkins with Docker

```bash
docker compose --profile ci up -d jenkins
```

Access:

- Jenkins: `http://localhost:8081`

The container mounts `/var/run/docker.sock` and `/usr/bin/docker` so Jenkins jobs can run `docker compose`.

## 4) Jenkins pipeline file

- Pipeline file: `Jenkinsfile`
- Main stages:
  1. Checkout
  2. Validate `.env` (required variables + optional SSL checks)
  3. Build Docker images
  4. Deploy with `docker compose up -d`
  5. Smoke test (`/` and readiness endpoint)

## 5) Basic operations

```bash
docker compose ps
docker compose logs -f edge-nginx
docker compose down
```

## 6) Certbot operation policy (short-term project)

If your project duration is under 30 days, it is usually fine to issue certs manually with certbot and mount the files.

- Recommended: run certbot once manually, verify files exist, then mount paths via `.env`
- Keep cert files private and never commit keys
- Set one calendar reminder around day 20-25 to verify expiration/renewal just in case
