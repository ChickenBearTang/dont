# AI SUBPROJECT GUIDE

## OVERVIEW
`backend/AI_TMP/ai` is an independent Python subproject (FastAPI + xAI/price engines + pytest). Treat this as a separate runtime from Java backend.

## STRUCTURE
```text
ai/
├── src/                 # runtime API/domain code
├── xai/                 # explainability and decision modules
├── price_engine/        # dataset/feature/schema logic
├── tests/               # pytest suite
├── scripts/             # data/regeneration helpers
└── pyproject.toml       # Python project deps
```

## WHERE TO LOOK
| Task | Location | Notes |
|---|---|---|
| API routes | `src/api/v1/routers/` | consumption/chat/strict_sec/xai_purchase |
| Runtime composition | `src/main.py` | FastAPI app + router mounting |
| xAI purchase pipeline | `xai/`, `src/domain/xai_purchase/` | reasoning/decision/contracts |
| Consumption report logic | `src/domain/consumption/` | report/anomaly/insights |
| Regression safety | `tests/` | `test_*.py` pattern |

## COMMANDS
```bash
cd backend/AI_TMP/ai && python -m pytest -q
cd backend/AI_TMP/ai/src && python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## CONVENTIONS
- Python indentation: 4 spaces.
- Keep API router code thin; put business logic in `src/domain/*`.
- Keep legacy experimental modules (`consumption_poc/`, root scripts) isolated from runtime paths unless intentionally migrated.

## ANTI-PATTERNS
- Do not import Java backend classes or conventions into Python runtime.
- Do not place new tests outside `tests/` unless it is a deliberate endpoint script case.
- Do not bypass schema/validator modules for training or inference payloads.

## CHILD GUIDE
- `src/AGENTS.md`
