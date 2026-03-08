# AI Consumption Report POC

이 프로젝트는 금융 서비스의 `소비 리포트`와 `AI 소비 분석`을 빠르게 검증하기 위한 POC다.
핵심 목적은 다음 두 가지다.

- 원천 금융 데이터를 기반으로 사람이 읽을 수 있는 소비 통계를 만든다.
- 통계와 이상탐지 결과를 바탕으로 LLM이 해설을 생성한다.

이 문서는 처음 프로젝트를 보는 사람이 전체 구조를 5분 안에 이해할 수 있도록 작성했다.

## 1. 한눈에 보는 구조

```mermaid
flowchart TD
    A[data/raw<br/>user_profile.json<br/>card_transactions.csv<br/>account_transactions.csv]
    B[src/consumption_poc/loader.py<br/>원천 데이터 로드]
    C[src/consumption_poc/reporting.py<br/>통계 집계]
    D[src/consumption_poc/anomaly.py<br/>이상탐지]
    E[src/consumption_poc/service.py<br/>리포트 조립]
    F[src/consumption_poc/ai_insights.py<br/>Gemini 해설]
    G[data/generated<br/>CSV/JSON 산출물]
    H[FastAPI API]
    I[frontend/index.html]

    A --> B --> C --> E
    B --> D --> E
    E --> F
    E --> G
    E --> H --> I
```

## 2. 현재 구현 범위

- 사용자 수: 8명
- 기간: 2025-10 ~ 2026-03
- 원천 데이터:
  - 카드 결제 내역
  - 계좌 입출금 내역
  - 사용자 프로필
- 산출물:
  - 기본 소비 리포트
  - 월간 목업형 통계 리포트
  - 규칙 기반 이상탐지
  - LLM 소비 분석

## 3. 폴더 구조

```text
ai/
├─ data/
│  ├─ raw/                  # 사람이 관리하는 원천 mock 데이터
│  └─ generated/            # 코드가 생성하는 통계/리포트 산출물
├─ docs/                    # 프로젝트 문서
├─ frontend/
│  └─ index.html            # 단일 페이지 프론트
├─ scripts/
│  ├─ generate_mock_raw_data.py
│  └─ regenerate_reports.py
├─ src/consumption_poc/
│  ├─ loader.py
│  ├─ reporting.py
│  ├─ anomaly.py
│  ├─ ai_insights.py
│  ├─ service.py
│  └─ main.py
└─ tests/
```

## 4. 이 프로젝트에서 중요한 원칙

- `raw`는 입력 데이터다.
- `generated`는 항상 코드로 다시 만들 수 있어야 한다.
- 수치 계산은 Python 코드가 책임진다.
- LLM은 숫자를 계산하는 주체가 아니라, 계산 결과를 해설하는 주체다.
- 프론트는 API와 generated 산출물을 읽는 소비자다.

## 5. 문서 읽는 순서

1. [architecture.md](c:\Users\SSAFY\S14P21A605\ai\docs\architecture.md)
2. [data-contract.md](c:\Users\SSAFY\S14P21A605\ai\docs\data-contract.md)
3. [api-spec.md](c:\Users\SSAFY\S14P21A605\ai\docs\api-spec.md)
4. [onboarding.md](c:\Users\SSAFY\S14P21A605\ai\docs\onboarding.md)
5. [worklog.md](c:\Users\SSAFY\S14P21A605\ai\docs\worklog.md)

## 5-1. 처음 보는 사람을 위한 3단계 이해법

### 1단계. raw와 generated를 구분한다

- `data/raw`는 사람이 만든 입력 데이터다.
- `data/generated`는 코드를 돌려 만든 출력 데이터다.
- 이 프로젝트를 이해할 때 가장 먼저 해야 할 일은 "무엇이 입력이고 무엇이 결과인지" 구분하는 것이다.

### 2단계. 숫자는 코드가 만들고 문장은 AI가 만든다고 이해한다

- `reporting.py`와 `anomaly.py`가 숫자를 만든다.
- `ai_insights.py`가 그 숫자를 읽고 해설 문장을 만든다.
- 따라서 숫자가 이상하면 먼저 코드와 raw를 보고, 문장이 이상하면 LLM 입력 payload를 봐야 한다.

### 3단계. 프론트는 두 개의 API를 조합해서 본다

- 월간 화면형 통계: `/api/v1/mock-consumption-stats`
- 종합 리포트와 AI 해설: `/api/v1/consumption-report`
- 즉 화면은 단일 API 하나가 아니라, 통계 API와 AI API를 같이 사용한다.

## 6. 빠른 실행

### raw 데이터 재생성

```bash
python scripts/generate_mock_raw_data.py
```

### generated 산출물 재생성

```bash
python scripts/regenerate_reports.py
```

### API 서버 실행

```bash
python -m uvicorn consumption_poc.main:app --host 127.0.0.1 --port 8000
```

### 테스트 실행

```bash
python -m pytest -q
```

## 7. 핵심 포인트

- `GET /api/v1/consumption-report`
  - 기존 종합 소비 리포트 + AI 해설
- `GET /api/v1/mock-consumption-stats`
  - 목업 화면에 맞춘 월간 통계
- `data/generated/users/<user_id>/<month>/...`
  - 사용자별 월간 목업 통계 산출물

## 8. 현재 상태

- raw 데이터 대량 생성 완료
- generated 산출물 사용자별/월별 생성 완료
- FastAPI 연동 완료
- 프론트 시각화 완료
- Playwright 수동 검증 완료
- pytest 통과 상태 유지

## 9. 문제를 볼 때 어디를 먼저 봐야 하는가

### 통계 숫자가 이상하다

1. `data/raw`의 입력값 확인
2. `src/consumption_poc/reporting.py` 집계 로직 확인
3. `data/generated` 산출물 확인
4. 프론트 렌더링 확인

### 이상탐지가 이상하다

1. `src/consumption_poc/anomaly.py` 규칙 확인
2. 거래 금액과 시간대가 raw에 어떻게 들어있는지 확인
3. `consumption_report_anomalies.csv` 확인

### AI 해설이 이상하다

1. `service.py`가 LLM에 넘기는 payload 확인
2. `ai_insights.py` 프롬프트와 모델 설정 확인
3. `llm_status`가 `ok`인지 `degraded`인지 확인
