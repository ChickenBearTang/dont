# 데이터 계약

## 디렉터리 규칙

- `data/raw`: 사람이 관리하는 정본 데이터
- `data/generated`: 코드가 생성하는 산출물

## Raw 데이터

### `user_profile.json`

- `user_id`: 사용자 식별자
- `name`: 사용자명
- `age`: 나이
- `job`: 직업
- `monthly_income`: 월소득
- `pay_day`: 급여일
- `residence_type`: 거주 형태
- `main_bank`: 주거래 은행
- `main_card_type`: 주 결제 수단

### `card_transactions.csv`

- `transaction_id`: 카드 거래 ID
- `user_id`: 사용자 ID
- `approved_at`: 승인 시각 ISO 8601
- `merchant_name`: 가맹점명
- `amount`: 결제 금액
- `category`: 대분류
- `subcategory`: 소분류
- `payment_method`: 결제수단
- `status`: 승인 상태
- `is_recurring`: 반복 결제 여부

### `account_transactions.csv`

- `transaction_id`: 계좌 거래 ID
- `user_id`: 사용자 ID
- `transacted_at`: 거래 시각 ISO 8601
- `type`: `in` 또는 `out`
- `counterparty`: 상대 거래처
- `amount`: 거래 금액
- `category`: 대분류
- `subcategory`: 소분류
- `balance_after`: 거래 후 잔액

## 정합성 규칙

- 모든 CSV/JSON은 UTF-8로 저장한다.
- `category`, `subcategory` 값은 영어 소문자 enum으로 유지한다.
- 같은 월의 카드 사용 합계와 같은 월의 `card_bill` 출금액은 정확히 일치해야 한다.
- `balance_after`는 거래 순서대로 계산해 맞아야 한다.
- generated 파일은 raw 기준으로 재생성되며 사람이 직접 수정하지 않는다.

## Generated 산출물

- `consumption_report_monthly.csv`
- `consumption_report_category.csv`
- `consumption_report_time.csv`
- `consumption_report_anomalies.csv`
- `cashflow_report_monthly.csv`
- `consumption_report_summary.json`
