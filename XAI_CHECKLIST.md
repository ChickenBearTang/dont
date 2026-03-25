# XAI Selective-Port Checklist

## Scope Guard

- [x] postgres 기본 경로 사용 (`run_workflow` 기본 backend)
- [x] sqlite는 명시적 선택 시 사용 가능 (`--backend sqlite`)
- [x] storage에 `PostgresCrawlStore`/`SqliteCrawlStore` 공존
- [x] manager에서 analyzer soft-fail fallback 지원
- [x] CLI no-flag 출력 shape 유지 (`{"source","item_count"}`)
- [x] CLI XAI 플래그 지원 (`--xai`, `--xai-top-k`)
- [x] finance profile optional fetch (`AI_FINANCE_API_URL`, `AI_FINANCE_API_TIMEOUT`)

## Test Contract

- [x] `ai.tests.test_run_workflow`
- [x] `ai.tests.test_postgres_store`
- [x] `ai.tests.test_ai_manager`
- [x] `ai.tests.test_ai_manager_xai`
- [x] `ai.tests.test_main_xai`
- [x] `ai.tests.test_main_finance_integration`
- [x] XAI canonical tests (`test_xai_*`)
- [x] price-engine tests (`test_price_engine_*`)

## Runtime Contract

- [x] `python -m ai` 실행 시 legacy JSON shape 유지
- [x] `python -m ai --xai` 실행 시 XAI envelope 출력
- [x] `python -m ai.crawler.run_workflow` 실행 시 postgres 기본 경로 사용
- [x] `python -m ai.crawler.run_workflow --backend sqlite` 정상
- [x] `python -m ai.crawler.run_workflow --backend postgres` 명시 선택 경로 정상
- [x] `python -m ai.check_xai_progress` import crash 없이 실행
