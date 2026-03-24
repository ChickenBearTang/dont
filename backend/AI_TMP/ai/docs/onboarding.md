# Onboarding Guide

## 이 문서의 목적

이 문서는 이 프로젝트를 처음 보는 사람이 "어디부터 봐야 하는지", "어떤 파일이 진짜 입력인지", "화면에 보이는 숫자가 어떻게 만들어지는지"를 빠르게 이해하도록 돕는다.

## 1. 먼저 알아야 할 핵심 개념 4개

### 1. raw는 사람이 만든 입력이다

- `data/raw/user_profile.json`
- `data/raw/card_transactions.csv`
- `data/raw/account_transactions.csv`

이 세 파일이 프로젝트의 시작점이다.  
화면에 보이는 통계와 AI 분석은 모두 이 파일들에서 출발한다.

### 2. generated는 코드가 만든 결과다

`data/generated` 아래 파일은 사람이 직접 작성한 정답지가 아니다.  
항상 raw를 읽어서 다시 만들 수 있어야 한다.

### 3. 숫자는 코드가 책임진다

- 합계
- 평균
- 비중
- 전월 비교
- 이상탐지 점수

이런 수치는 모두 Python 코드가 계산한다.  
숫자가 틀렸다면 LLM보다 집계 코드를 먼저 의심해야 한다.

### 4. AI는 해설을 책임진다

LLM은 거래 내역 전체를 무제한으로 읽고 판단하는 구조가 아니다.  
현재는 코드가 만든 통계 요약과 이상탐지 결과를 입력으로 받아 설명 문장을 생성한다.

## 2. 실제로 화면 하나가 만들어지는 과정

예를 들어 사용자가 `Kim Minsoo`, `2026-02`를 선택했다고 가정한다.

```mermaid
flowchart TD
    A[사용자 선택: Kim Minsoo / 2026-02]
    B[/api/v1/mock-consumption-stats 호출]
    C[service.py - build_mock_statistics]
    D[reporting.py - 월간 통계 생성]
    E[period_summary.json + daily_cumulative + category_breakdown]
    F[프론트 월간 통계 화면 렌더링]
    G[/api/v1/consumption-report 호출]
    H[service.py - build_report]
    I[anomaly.py + ai_insights.py]
    J[AI 분석 섹션 렌더링]

    A --> B --> C --> D --> E --> F
    A --> G --> H --> I --> J
```

즉 화면은 한 번에 하나의 API만 보는 것이 아니라,

- 월간 통계용 API
- AI 해설용 API

두 개를 나눠서 본다.

## 3. 파일을 읽는 추천 순서

### 1순위. 프로젝트 전체 개요

- [README.md](c:\Users\SSAFY\S14P21A605\ai\README.md)

### 2순위. 아키텍처와 데이터 흐름

- [architecture.md](c:\Users\SSAFY\S14P21A605\ai\docs\architecture.md)

### 3순위. 데이터 정의

- [data-contract.md](c:\Users\SSAFY\S14P21A605\ai\docs\data-contract.md)

### 4순위. API 정의

- [api-spec.md](c:\Users\SSAFY\S14P21A605\ai\docs\api-spec.md)

### 5순위. 실제 구현 파일

- [main.py](c:\Users\SSAFY\S14P21A605\ai\src\consumption_poc\main.py)
- [service.py](c:\Users\SSAFY\S14P21A605\ai\src\consumption_poc\service.py)
- [reporting.py](c:\Users\SSAFY\S14P21A605\ai\src\consumption_poc\reporting.py)
- [anomaly.py](c:\Users\SSAFY\S14P21A605\ai\src\consumption_poc\anomaly.py)
- [ai_insights.py](c:\Users\SSAFY\S14P21A605\ai\src\consumption_poc\ai_insights.py)
- [index.html](c:\Users\SSAFY\S14P21A605\ai\frontend\index.html)

## 4. 폴더별 역할

### `data/raw`

- 사람이 설계하는 mock 금융 데이터
- 프로젝트의 유일한 원천 입력

### `data/generated`

- raw를 기반으로 계산된 통계와 리포트 결과
- 회귀 검증과 프론트 표시용

### `src/consumption_poc`

- 분석의 핵심 로직
- API 서버
- LLM 연동

### `frontend`

- 사용자에게 보이는 소비 리포트 화면
- 순수 소비자 역할

### `scripts`

- raw 대량 생성
- generated 재생성

### `tests`

- 데이터 정합성
- API 응답
- 사용자 선택 로직

## 5. 자주 헷갈리는 포인트

### Q1. raw도 mock이고 generated도 mock인가

아니다.

- raw는 mock 입력 데이터
- generated는 그 입력을 기반으로 실제 코드가 계산한 출력

즉 generated는 "가짜 입력"이 아니라 "계산 결과"다.

### Q2. LLM이 raw 전체를 읽나

현재는 아니다.

- 코드가 먼저 통계/이상탐지를 만든다.
- LLM은 그 요약 payload를 받아 해설한다.

### Q3. 프론트에 보이는 숫자는 어디서 오나

- 월간 목업형 숫자: `/api/v1/mock-consumption-stats`
- AI 분석 문장: `/api/v1/consumption-report`

### Q4. generated root 파일과 사용자별 파일은 왜 둘 다 있나

- root 파일은 전체 구조를 빠르게 확인하는 대표 산출물
- 사용자별 파일은 실제 화면과 월간 리포트 확인용 산출물

## 6. 개발자가 문제를 추적하는 방법

### 케이스 1. 특정 사용자의 월간 총소비가 이상하다

1. `data/raw/card_transactions.csv`에서 해당 사용자, 해당 월 거래를 필터링한다.
2. `reporting.py`의 월별 합산 로직을 본다.
3. `data/generated/users/<user_id>/<month>/period_summary.json`을 본다.
4. 프론트에서 같은 사용자/월을 선택해 값이 같은지 본다.

### 케이스 2. 카테고리 통계가 이상하다

1. raw의 `category`, `subcategory`를 확인한다.
2. `data-contract.md`의 재분류 규칙을 본다.
3. `reporting.py`의 화면용 카테고리 매핑을 확인한다.
4. `category_breakdown.csv` 결과를 확인한다.

### 케이스 3. AI 분석이 밋밋하다

1. `service.py`의 LLM 입력 payload를 확인한다.
2. `ai_insights.py`의 프롬프트 구조를 본다.
3. 필요하면 representative raw sample을 추가 설계한다.

## 7. 실행 순서

### 1. raw 데이터 생성 또는 확인

```bash
python scripts/generate_mock_raw_data.py
```

### 2. generated 산출물 생성

```bash
python scripts/regenerate_reports.py
```

### 3. 서버 실행

```bash
cd src
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 4. 테스트 실행

```bash
python -m pytest -q
```

## 8. 앞으로 확장할 때의 기준

- raw와 generated의 경계를 흐리지 않는다.
- 숫자는 코드가 계산한다.
- AI는 해설에 집중한다.
- 프론트는 통계와 AI 결과를 명확히 구분해서 보여준다.
- 문서 수정 없이 새 구조를 넣지 않는다.
