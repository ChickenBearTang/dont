# FRONTEND GUIDE

## OVERVIEW
`frontend/` is a Vite + React 19 + TypeScript app. Main split is feature modules (`src/features`) and shared primitives (`src/shared`).

## STRUCTURE
```text
frontend/
├── src/app/          # router + app composition
├── src/features/     # domain feature slices
├── src/shared/       # reusable api/components/hooks/utils
├── eslint.config.js
├── .prettierrc
└── package.json
```

## WHERE TO LOOK
| Task | Path | Notes |
|---|---|---|
| Route changes | `src/app/router.tsx` | central route graph |
| Feature behavior | `src/features/<feature>/` | API/hooks/pages near each feature |
| Reusable UI/helpers | `src/shared/` | used across feature boundaries |

## COMMANDS
```bash
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint
```

## CONVENTIONS
- Formatting: Prettier (`singleQuote: true`, `printWidth: 100`, `tabWidth: 2`).
- ESLint flat config for TS/TSX + react hooks rules.
- Pre-commit via lint-staged:
  - `*.{ts,tsx,js,jsx}` => `eslint --fix`, `prettier --write`
  - `*.{json,css,md}` => `prettier --write`

## ANTI-PATTERNS
- Do not place feature-specific business logic under `src/shared`.
- Do not bypass route lazy-loading patterns used in `src/app/router.tsx`.
- Do not commit `dist/` output as source.

## CHILD GUIDES
- `src/features/AGENTS.md`
- `src/shared/AGENTS.md`
