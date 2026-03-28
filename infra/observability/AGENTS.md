# OBSERVABILITY GUIDE

## OVERVIEW
`infra/observability` defines log collection and dashboards for local stack monitoring.

## STRUCTURE
```text
observability/
├── loki/loki-config.yaml
├── alloy/config.alloy
└── grafana/provisioning/
    ├── datasources/loki.yaml
    └── dashboards/{dashboards.yaml, app-overview.json}
```

## WHERE TO LOOK
| Need | Path |
|---|---|
| Loki ingestion/storage settings | `loki/loki-config.yaml` |
| Log scraping pipeline | `alloy/config.alloy` |
| Grafana datasource registration | `grafana/provisioning/datasources/loki.yaml` |
| Dashboard provisioning | `grafana/provisioning/dashboards/` |

## CONVENTIONS
- Provisioning files should stay deterministic and boot-time loadable.
- Dashboard JSON updates should align with `dashboards.yaml` provisioning entries.

## ANTI-PATTERNS
- Do not mix app runtime secrets into observability config files.
- Do not add manual Grafana UI-only state without syncing provisioning files.
- Do not break Loki endpoint contract expected by datasource config.
