# INFRA GUIDE

## OVERVIEW
`infra/` holds edge routing (nginx) and observability stack configuration (loki/grafana/alloy).

## STRUCTURE
```text
infra/
├── nginx/
│   ├── nginx.conf
│   ├── http.conf
│   ├── https.conf
│   └── entrypoint-nginx.sh
└── observability/
    ├── loki/
    ├── grafana/
    └── alloy/
```

## WHERE TO LOOK
| Change | Path | Notes |
|---|---|---|
| Edge routing/TLS behavior | `nginx/*.conf`, `nginx/entrypoint-nginx.sh` | TLS path controlled by env + mounted certs |
| Compose integration | `../docker-compose.yml` | services: edge-nginx/loki/alloy/grafana |
| Observability specifics | `observability/` | use child guide for details |

## CONVENTIONS
- Keep nginx config split by protocol mode (`http.conf` vs `https.conf`).
- Keep observability provisioning files declarative and versioned.

## ANTI-PATTERNS
- Do not hardcode cert file paths outside compose/env contract.
- Do not couple app business config into infra files.
- Do not edit generated dashboard runtime state as source-of-truth.

## CHILD GUIDE
- `observability/AGENTS.md`
