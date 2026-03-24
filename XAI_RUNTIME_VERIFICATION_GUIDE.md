# XAI Runtime Verification Guide

## 1) Environment

`.env.example`의 AI 네임스페이스를 기준으로 환경을 설정합니다.

- `AI_POSTGRES_DSN` (우선)
- 또는 `AI_POSTGRES_HOST`, `AI_POSTGRES_PORT`, `AI_POSTGRES_DB`, `AI_POSTGRES_USER`, `AI_POSTGRES_PASSWORD`
- `AI_FINANCE_API_URL` (옵션)
- `AI_FINANCE_API_TIMEOUT` (기본 3)

## 2) Core CLI Smoke

```bash
cd backend/AI_TMP
python -m ai
python -m ai --xai
python -m ai --xai --xai-top-k 4
```

기대 결과:

- no-flag: `source`, `item_count` 키만 포함
- `--xai`: XAI envelope(`schema_version`, `crawl`, `errors` 등) 포함

## 3) Workflow Backend Smoke

```bash
cd backend/AI_TMP
python -m ai.crawler.run_workflow --max-pages 1
python -m ai.crawler.run_workflow --backend sqlite --db-path ai/data/crawl.db --max-pages 1
python -m ai.crawler.run_workflow --backend postgres --db-url postgresql://ai_user:ai_password@127.0.0.1:55432/ai_crawl --max-pages 1
```

기대 결과:

- 기본 backend는 postgres로 동작
- sqlite는 `--backend sqlite`를 명시했을 때만 동작

## 4) Deterministic Progress Check

```bash
cd backend/AI_TMP
python -m ai.check_xai_progress
```

기대 결과:

- import/entrypoint/기본 XAI payload shape를 JSON 요약으로 보고
- 실패 시 `ok=false`와 실패 단계/이유를 반환

## 5) Test Suite

```bash
cd backend/AI_TMP
python -m unittest discover -s ai/tests -v
```

필요 시 핵심 스모크만 별도 실행:

```bash
python -m unittest ai.tests.test_ai_manager ai.tests.test_ai_manager_xai ai.tests.test_main_xai ai.tests.test_main_finance_integration ai.tests.test_run_workflow -v
```
