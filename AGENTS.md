# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-26 (Asia/Seoul)
**Mode:** update

## OVERVIEW
Single repo with 4 execution surfaces: Spring Boot backend (`backend/`), Python AI service (`backend/AI_TMP/ai/`), React/Vite frontend (`frontend/`), infra/observability (`infra/`, `docker-compose.yml`).

## STRUCTURE
```text
./
├── backend/                  # Java API + AI Python subproject
│   ├── src/main/java/...     # Spring Boot domain modules
│   └── AI_TMP/ai/            # FastAPI + xAI + pytest suite
├── frontend/                 # React 19 + Vite 7 + TS
├── infra/                    # nginx + loki/grafana/alloy
├── docker-compose.yml        # local integration topology
└── Jenkinsfile               # CI build/deploy/smoke flow
```

## WHERE TO LOOK
| Task | Location | Notes |
|---|---|---|
| Java backend API/domain change | `backend/src/main/java/com/ssafy/edu/awesomeproject/domain/` | Domain split: auth/community/fin/notification/ranking/user |
| Python AI API change | `backend/AI_TMP/ai/src/` | FastAPI entry: `src/main.py` |
| AI model/xAI behavior | `backend/AI_TMP/ai/xai/`, `backend/AI_TMP/ai/tests/` | Price/XAI test coverage concentrated here |
| Frontend feature flow | `frontend/src/features/` | Route graph in `frontend/src/app/router.tsx` |
| Frontend shared primitives | `frontend/src/shared/` | shared components/hooks/utils used cross-feature |
| Edge/infra behavior | `infra/nginx/`, `infra/observability/` | nginx TLS toggle + loki/grafana/alloy config |

## CONVENTIONS (PROJECT-SPECIFIC)
- Indentation: 2 spaces (JS/TS/JSON/CSS/MD), 4 spaces (Java/Python).
- Frontend formatting: Prettier (`singleQuote: true`, `printWidth: 100`) + ESLint on staged files.
- Backend Java formatting: Spotless + `googleJavaFormat().aosp()`.
- Python AI runtime is a separate subproject under `backend/AI_TMP/ai` with its own `pyproject.toml`.

## ANTI-PATTERNS (THIS PROJECT)
- Do not mix Java backend domain logic into `backend/AI_TMP/ai`; treat as separate runtime boundaries.
- Do not commit generated/build artifacts as source of truth (`backend/build/`, `frontend/dist/`, runtime-generated data).
- Do not duplicate parent AGENTS content in child AGENTS; child files must contain local-only guidance.
- Do not assume frontend tests exist globally; current dense test conventions are primarily Python pytest under `backend/AI_TMP/ai/tests`.

## COMMANDS
```bash
# Frontend
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint

# Java backend
cd backend && ./gradlew test
cd backend && ./gradlew bootJar

# Python AI service
cd backend/AI_TMP/ai && python -m pytest -q
cd backend/AI_TMP/ai/src && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Integrated local stack
docker compose up -d ai-postgres ai-python
docker compose up -d redis backend frontend edge-nginx loki alloy grafana
```

## HIERARCHY
- `backend/AGENTS.md`
  - `backend/src/main/java/com/ssafy/edu/awesomeproject/domain/AGENTS.md`
  - `backend/AI_TMP/ai/AGENTS.md`
    - `backend/AI_TMP/ai/src/AGENTS.md`
- `frontend/AGENTS.md`
  - `frontend/src/features/AGENTS.md`
  - `frontend/src/shared/AGENTS.md`
- `infra/AGENTS.md`
  - `infra/observability/AGENTS.md`

## NOTES
- LSP availability is partial in this environment (Python symbols available; TS/Java servers absent), so symbol density scoring was merged with directory/file-density evidence.
- AGENTS placement followed domain boundaries first, then complexity hotspots.
