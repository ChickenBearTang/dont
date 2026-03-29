# FEATURE LAYER GUIDE

## OVERVIEW
`src/features` contains product domains. Keep feature logic local: api + hooks + pages + types under the same feature tree.

## STRUCTURE
```text
features/
├── auth/
├── user/
├── finance/
├── community/
├── ranking/
├── point/
└── ai/
```

## WHERE TO LOOK
| Domain | Typical paths |
|---|---|
| Finance | `finance/account`, `finance/card`, `finance/report`, `finance/pages` |
| Auth | `auth/pages`, `auth/store`, `auth/utils` |
| Community | `community/pages`, `community/components`, `community/types` |
| User | `user/pages`, `user/components`, `user/*` subdomains |

## CONVENTIONS
- Keep feature API clients inside the feature (`feature/api/*`).
- Keep feature-local types with the feature; export through feature index when needed.
- Cross-feature reuse belongs to `src/shared`, not other feature directories.

## ANTI-PATTERNS
- Do not import private internals of another feature directly.
- Do not centralize all API calls into a feature-agnostic dumping file.
- Do not move feature pages into `src/pages` unless app-level routing requires it.
