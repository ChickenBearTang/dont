# SHARED LAYER GUIDE

## OVERVIEW
`src/shared` is for cross-feature building blocks only: API core, reusable components, hooks, utils, and common types.

## STRUCTURE
```text
shared/
├── api/
├── components/
├── hooks/
├── store/
├── types/
└── utils/
```

## WHERE TO LOOK
| Purpose | Path |
|---|---|
| HTTP/query primitives | `api/axiosInstance.ts`, `api/queryClient.ts` |
| UI primitives | `components/` |
| Reusable hooks | `hooks/` |
| Cross-feature helpers | `utils/` |

## CONVENTIONS
- Shared code must be feature-agnostic and reusable.
- Keep barrel exports minimal; avoid circular exports in `index.ts` files.
- Utilities should stay small and single-purpose.

## ANTI-PATTERNS
- Do not place feature/domain rules in shared hooks or utils.
- Do not create hidden side effects in shared helpers.
- Do not let shared components depend on feature-specific stores.
