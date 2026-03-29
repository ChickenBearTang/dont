# AI RUNTIME (`src/`) GUIDE

## OVERVIEW
`src/` is the production FastAPI runtime surface. Keep execution entry, routers, and domain services cohesive here.

## STRUCTURE
```text
src/
├── main.py
├── api/v1/routers/
├── domain/
│   ├── chat/
│   ├── consumption/
│   ├── strict_secretary/
│   └── xai_purchase/
└── utils/
```

## WHERE TO LOOK
| Change | Path |
|---|---|
| New endpoint | `api/v1/routers/` |
| Business logic | `domain/<feature>/` |
| Shared IO helpers | `utils/` |
| App wiring | `main.py` |

## CONVENTIONS
- Router files should orchestrate request/response only.
- Domain modules own validation and core decisions.
- Keep import paths stable from `main.py` router registration.

## TEST TARGETS
- `backend/AI_TMP/ai/tests/test_api.py`
- `backend/AI_TMP/ai/tests/test_service.py`
- feature-specific `test_xai_*`, `test_price_engine_*` suites.

## ANTI-PATTERNS
- Do not place heavy data transformation in router handlers.
- Do not duplicate logic between `domain/*` and legacy root modules.
- Do not remove fallback/error paths in agent/model wrappers.
