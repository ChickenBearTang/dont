# JAVA DOMAIN GUIDE

## OVERVIEW
Domain package holds business boundaries for Spring backend. Each subdirectory maps to a product context.

## STRUCTURE
```text
domain/
├── auth/
├── community/
├── fin/
├── notification/
├── ranking/
└── user/
```

## WHERE TO LOOK
| Work type | Path |
|---|---|
| Auth/session/token | `auth/` |
| Profile/onboarding | `user/` |
| Finance/account/card/consumption | `fin/` |
| Community posts/comments/reports | `community/` |
| Notification + SSE | `notification/` |
| Ranking + SSE events | `ranking/` |

## CONVENTIONS
- Keep controller/service/repository layering inside each domain.
- Preserve domain-local DTO/error packages rather than global dumping.
- Keep external integrations in designated adapter/client packages.

## TESTING
- Prefer domain-matching tests under `backend/src/test/java/.../domain/<same-domain>/`.

## ANTI-PATTERNS
- Do not cross-call unrelated domain internals directly when an app/service boundary exists.
- Do not mix API contract DTOs with persistence entities in the same type.
- Do not move domain rules into `global/` for convenience.
