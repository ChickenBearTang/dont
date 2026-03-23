# XAI 런타임 검증 가이드

이 문서는 `python -m ai --xai` 활성 경로 기준으로
Spring 재무 연동, SHAP, DiCE, 의사결정 분기, 회귀 테스트를 순차 검증하는 절차입니다.

## 0) 사전 준비

```bash
pip install shap dice-ml
```

> 이미 설치되어 있으면 생략 가능합니다.

---

## 1) 활성 경로 기본 계약 확인

```bash
python -m ai --xai --top-k 2
```

### 통과 기준

- 출력 JSON 루트에 아래 키가 존재해야 합니다.
  - `schema_version`
  - `explanations`
  - `analysis`

---

## 2) Spring 재무 연동 성공/실패 fallback 확인

### 2-1. Spring API 성공 경로

```bash
python -m unittest ai.tests.test_main_finance_integration.MainFinanceIntegrationTest.test_main_uses_spring_finance_profile_when_api_succeeds -v
```

### 통과 기준

- 테스트 통과
- `analysis.finance_profile_source == "spring_api"`

### 2-2. Spring API 실패 fallback 경로

```bash
python -m unittest ai.tests.test_main_finance_integration.MainFinanceIntegrationTest.test_main_falls_back_to_cli_finance_profile_on_api_failure -v
```

### 통과 기준

- 테스트 통과
- `analysis.finance_profile_source == "cli_default_fallback"`

---

## 3) SHAP/DiCE 런타임 메타데이터 확인

```bash
python -m unittest ai.tests.test_xai_runtime_engines -v
```

### 통과 기준

- `analysis.runtime_engines.shap` 존재
- `analysis.runtime_engines.dice` 존재
- 각 엔진에 `enabled`, `backend` 필드 존재

---

## 4) 의사결정 4분기 분기 커버리지 확인

```bash
python -m unittest ai.tests.test_xai_decision_engine -v
```

### 통과 기준

- `BUY_NOW`, `WAIT`, `NOT_RECOMMENDED`, `REVIEW` 각 분기 테스트 통과

---

## 5) 전체 XAI 회귀 테스트 확인

```bash
python -m unittest discover -s ai/tests -p "test_*xai*.py"
```

### 통과 기준

- 전체 테스트가 `OK`

---

## 6) 요청된 기본 회귀 세트 확인

```bash
python -m unittest ai.tests.test_crawler_hot_deal ai.tests.test_main_xai
```

### 통과 기준

- 전체 테스트가 `OK`

---

## 7) 자동 중간점검 스크립트 확인

```bash
python ai/check_xai_progress.py
```

### 통과 기준

- `XAI progress checks passed` 출력

---

## 8) (선택) 실크롤 기반 런타임 실증

```bash
python -m ai --xai --real-crawl --top-k 3
```

### 확인 포인트

- `item_count > 0`
- `analysis.runtime_engines` 상태 확인
  - 예: `shap.enabled == true`
  - 예: `dice.enabled == true` 또는 fallback 사유(`reason`) 명시

---

## 권장 실행 순서 요약

1. `python -m ai --xai --top-k 2`
2. `python -m unittest ai.tests.test_main_finance_integration -v`
3. `python -m unittest ai.tests.test_xai_runtime_engines -v`
4. `python -m unittest ai.tests.test_xai_decision_engine -v`
5. `python -m unittest discover -s ai/tests -p "test_*xai*.py"`
6. `python -m unittest ai.tests.test_crawler_hot_deal ai.tests.test_main_xai`
7. `python ai/check_xai_progress.py`
8. (선택) `python -m ai --xai --real-crawl --top-k 3`
