# Data Directory Guide

## 목적

`data/`는 이 프로젝트의 입력과 출력이 모이는 디렉터리다.

## 구조

```text
data/
├─ raw/
│  ├─ user_profile.json
│  ├─ card_transactions.csv
│  └─ account_transactions.csv
└─ generated/
   ├─ consumption_report_monthly.csv
   ├─ consumption_report_category.csv
   ├─ consumption_report_time.csv
   ├─ consumption_report_anomalies.csv
   ├─ cashflow_report_monthly.csv
   ├─ consumption_report_summary.json
   └─ users/
      └─ <user_id>/
         └─ <month>/
```

```mermaid
flowchart LR
    A[data/raw] --> B[Python 집계 로직]
    B --> C[data/generated]
    C --> D[API]
    D --> E[Frontend]
```

## raw

사람이 설계하고 유지하는 입력 데이터다.

- 수정 대상
- mock 데이터
- 분석의 시작점

## generated

코드가 raw를 읽어 계산한 출력 데이터다.

- 직접 수정하지 않는다
- 항상 재생성 가능해야 한다
- 프론트, API, 검증에 사용된다

### 포함되는 것

- 월별 소비 합계
- 카테고리 비중
- 시간대/요일 통계
- 이상거래 후보
- 사용자별 월간 목업 산출물

### 포함되지 않는 것

- 사람이 수동으로 적은 최종 통계값
- 사람이 수동으로 수정한 AI 해설
- raw와 무관한 임의 숫자

## 재생성 방법

### raw 데이터 새로 만들기

```bash
python scripts/generate_mock_raw_data.py
```

### generated 다시 만들기

```bash
python scripts/regenerate_reports.py
```

## 예시

`data/generated/users/U1001/2026-02/` 아래에는 다음이 들어간다.

- `period_summary.json`
- `daily_cumulative.csv`
- `category_breakdown.csv`
- `six_month_trend.csv`
- `six_month_summary.json`
