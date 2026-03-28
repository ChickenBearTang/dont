# BACKEND KNOWLEDGE BASE

## OVERVIEW
`backend/` contains two runtimes: Spring Boot Java app and an embedded Python AI subproject (`AI_TMP/ai`). Treat them as separate execution boundaries.

## STRUCTURE
```text
backend/
├── src/main/java/com/ssafy/edu/awesomeproject/  # Spring Boot code
├── src/test/java/...                             # JUnit tests
├── AI_TMP/ai/                                    # FastAPI + pytest runtime
├── build.gradle                                  # Java deps + Spotless
└── gradlew                                       # Gradle wrapper
```

## WHERE TO LOOK
| Task | Location | Notes |
|---|---|---|
| Java domain logic | `src/main/java/com/ssafy/edu/awesomeproject/domain/` | auth/community/fin/notification/ranking/user |
| Java app bootstrap | `src/main/java/.../AwesomeProjectApplication.java` | `@SpringBootApplication` entry |
| Java tests | `src/test/java/` | JUnit + Testcontainers usage |
| AI runtime work | `AI_TMP/ai/` | Use AI subproject docs, not Java conventions |

## COMMANDS
```bash
cd backend && ./gradlew test
cd backend && ./gradlew bootJar
```

## CONVENTIONS
- Java formatting enforced by Spotless (`googleJavaFormat().aosp()`, unused import removal).
- Java toolchain target is 21 (`build.gradle`).
- Domain package is the primary ownership boundary.

## ANTI-PATTERNS
- Do not add Python runtime code under `src/main/java`.
- Do not apply Java build output (`build/`) as source-of-truth edits.
- Do not put cross-domain business logic directly into controllers; keep in domain services.

## CHILD GUIDES
- `src/main/java/com/ssafy/edu/awesomeproject/domain/AGENTS.md`
- `AI_TMP/ai/AGENTS.md`
