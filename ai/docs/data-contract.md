# Data Contract

## 1. 데이터 구분

이 프로젝트에는 두 종류의 데이터가 있다.

### raw

- 사람이 설계한 원천 mock 데이터
- 분석의 입력
- 수정 대상

### generated

- raw를 코드로 계산해서 만든 결과
- 분석의 출력
- 직접 수정 대상 아님

## 2. raw 파일

### `data/raw/user_profile.json`

사용자 목록.

필드:

- `user_id`
- `name`
- `age`
- `job`
- `monthly_income`
- `pay_day`
- `residence_type`
- `main_bank`
- `main_card_type`

### `data/raw/card_transactions.csv`

카드 결제 원천 데이터.

필드:

- `transaction_id`
- `user_id`
- `approved_at`
- `merchant_name`
- `amount`
- `category`
- `subcategory`
- `payment_method`
- `status`
- `is_recurring`

### `data/raw/account_transactions.csv`

계좌 입출금 원천 데이터.

필드:

- `transaction_id`
- `user_id`
- `transacted_at`
- `type`
- `counterparty`
- `amount`
- `category`
- `subcategory`
- `balance_after`

## 3. raw 데이터 규칙

- 모든 파일은 UTF-8이다.
- 카드 결제는 `status=approved`인 거래만 소비 통계에 반영한다.
- 월별 카드 사용 합계와 `card_bill` 출금액은 사용자별로 일치해야 한다.
- `balance_after`는 거래 순서대로 계산 가능해야 한다.
- generated는 raw에서 항상 재생성 가능해야 한다.

## 4. generated 파일

### root 산출물

- `consumption_report_monthly.csv`
- `consumption_report_category.csv`
- `consumption_report_time.csv`
- `consumption_report_anomalies.csv`
- `cashflow_report_monthly.csv`
- `consumption_report_summary.json`

### 사용자별 목업 산출물

경로:

```text
data/generated/users/<user_id>/<month>/
```

파일:

- `period_summary.json`
- `daily_cumulative.csv`
- `category_breakdown.csv`
- `six_month_trend.csv`
- `six_month_summary.json`

## 5. 카테고리 재분류 규칙

목업 화면용 카테고리 표시는 raw `category/subcategory`를 그대로 쓰지 않는다.
화면 친화적인 label로 재분류한다.

예:

- `ecommerce` -> `온라인쇼핑`
- `shopping/*` -> `오프라인쇼핑`
- `fuel/taxi/public_transit` -> `교통/주유`
- `cafe` -> `커피`
- `convenience_store` -> `편의점`
- `fastfood` -> `패스트푸드`
- `delivery/dining/groceries` -> `음식점`
- `medical/fitness` -> `의료`

## 6. generated 산출물의 의미

### `period_summary.json`

- 선택 월 총소비
- 전월 총소비
- 차이 금액
- 증감 방향
- UI 문구용 비교 텍스트

### `daily_cumulative.csv`

- 날짜별 누적 소비
- 선택 월과 전월의 누적 비교선용 데이터

### `six_month_trend.csv`

- 최근 6개월 월별 소비
- 선택 월 여부 표시

### `six_month_summary.json`

- 최근 6개월 평균 소비 금액
- 차트용 월 목록

### `category_breakdown.csv`

- 화면용 카테고리명
- 금액
- 비중
- 전월 금액
- 전월 대비 차이 금액

## 7. LLM 입력 계약

LLM은 raw 전체를 읽지 않는다.

현재 입력 구조:

- `overview`
- `monthly`
- `top_categories`
- `top_subcategories`
- `time_patterns`
- `cashflow`
- `anomalies`
- `fallback_analysis`

즉 LLM 입력은 `통계 요약 payload`다.
