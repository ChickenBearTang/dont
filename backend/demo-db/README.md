# demo DB — 가격 모델·구매 평가 시연용 가짜 데이터

운영 DB(크롤링 원본 `crawl_items`, Spring 금융 테이블)에 접근할 수 없을 때, **같은 스키마의 가짜 DB 두 개**를 로컬에서 만들어
구매 평가 흐름(Spring → AI)을 끝까지 돌려 보기 위한 도구다.

> **전부 가짜다.** 사용자·거래·시세 모두 생성기가 만든 값이고 실제와 무관하다. 이 데이터로 모델을 학습해 점수를 내면
> 그것은 "이 생성기의 모양을 따라 하는 정도"이지 실제 예측력이 아니다. 운영 DB 에 넣지 않는다 (아래 안전장치).

| DB | 어디 | 안에 든 것 |
|---|---|---|
| **금융** (`finance`) | Spring 본 DB (`DB_URL`) | `cohorts`, `users`, `accounts`, `account_transactions`, `savings_settings`, `cards`, `card_transactions` — 가상 사용자 12명 |
| **가격** (`crawl`) | ai-postgres (`AI_POSTGRES_*`) | `crawl_items` — 제품 3개(F87, MX Master 3S, VXE R1)의 120일 핫딜 글 427건 |

## 쓰는 법

필요한 것: Python 3.11+, `psql`, 그리고 빈 PostgreSQL 데이터베이스 하나씩.

```bash
# 가상 사용자 표 (소득, 고정지출, 30일 카드 사용, 기대 예산 상태)
python3 backend/demo-db/demo.py summary

# 스키마 + 시드 적재. 이미 있던 데모 행은 먼저 지우고 다시 넣는다 (여러 번 돌려도 안전)
python3 backend/demo-db/demo.py load \
  --finance-dsn postgresql://user:pw@localhost:5432/finance_demo \
  --crawl-dsn   postgresql://user:pw@localhost:55432/ai_crawl

# 시드 SQL 파일만 만들고 싶을 때 (backend/demo-db/build/, git 에 올라가지 않음)
python3 backend/demo-db/demo.py generate

# 데모 행만 지우기
python3 backend/demo-db/demo.py unload --finance-dsn ... --crawl-dsn ...
```

**며칠에 한 번 다시 적재한다.** Spring 은 `LocalDate.now()` 로 "이번 달"·"최근 3개월"을 계산하고 AI 는 "최근 30일"을 센다.
시드의 날짜는 `--as-of`(기본: 오늘)에서 거꾸로 센 절대 날짜라서, 오래 두면 낡는다. 같은 `load` 를 다시 돌리면 된다.

Spring 이 이 DB 를 쓰게 하려면 `DB_URL`(`DB_USERNAME`, `DB_PASSWORD`)을 금융 demo DB 로, `AI_POSTGRES_HOST/PORT/DB/USER/PASSWORD`
(`PrXaiAvailabilityService` 가 직접 읽는다)를 가격 demo DB 로 지정한다. 이 연결은 실제로 띄워서 확인했다 (아래 "Spring 까지 실제로 돌린 결과").

### 안전장치

- `load`/`unload` 는 DSN 의 호스트가 `localhost`/`127.0.0.1`/`::1`/유닉스 소켓/`demo…` 로 시작하는 이름이 아니면 **거부**한다.
  정말 데모 DB 면 `--force`.
- 데모 행은 알아보기 쉽게 만들었다: 이메일 `demo-dNN@demo.invalid`(예약 도메인), 계좌·카드 번호 `DEMO-…`,
  크롤 행의 `source`/`url` 이 `https://demo.invalid/…`. 지우는 기준도 이것이다. 데모 코호트(`DEMO`, 9999기)는 남는다.
- 데모 사용자 비밀번호는 `demo-pass-1234` 로 공개되어 있다 (BCrypt 해시가 시드에 들어 있다). 그래서 운영에 넣으면 안 된다.

## 가상 사용자 12명 (설계값)

130,000원짜리(마우스·키보드 정도)를 샀을 때의 5·3·2 예산 상태를 기준으로 손으로 정한 사람들이다. 소득·고정지출은 Spring DB 에
컬럼이 없어서 **계좌 거래(급여 입금, 월세·통신비·공과금·보험·자동저축 출금)로 남겼다.** 잔액은 기준일에 따라 달라지므로
`demo.py summary` 로 본다. 기대 상태가 맞는지는 테스트가 실제 `budget_rule.assess_budget` 로 확인한다.

계좌 거래의 적요는 Spring 원장(`LedgerSummaries`)이 남기는 문구와 같다. `(자동저축) 출금/입금`, `(이월) …` 처럼 괄호로 시작하는
적요는 본인 계좌 사이의 이동이라 소득·지출로 세지 않고, 소득·고정지출 추정(`MonthlyBudgetBasisEstimator`)이 이 규칙으로 읽는다.
`(자동저축) 출금`만은 매달 쌓는 비상금이라 고정지출에 넣는다.

| id | 유형 | 월 소득 | 고정지출 | 30일 카드 | 기대 상태 | 요점 |
|---|---|---:|---:|---:|---|---|
| d01 | 사회초년생 | 2,500,000 | 600,000 | 200,000 | within | 한도는 여유, 비상금 1.5개월치(`EMERGENCY_COVER_LOW`) |
| d02 | 사회초년생 | 2,200,000 | 620,000 | 280,000 | tight | 구매 후 93.6% → WAIT |
| d03 | 20대 후반 | 3,200,000 | 900,000 | 300,000 | within | 평범한 여유 |
| d04 | 20대 후반 | 3,000,000 | 900,000 | 500,000 | over | 지금은 93%, 이번 구매로 102% |
| d05 | 30대 초반 | 4,500,000 | 1,200,000 | 450,000 | within | 비상금 5.5개월치 |
| d06 | 30대 초반 | 3,800,000 | 1,150,000 | 850,000 | already_over | 구매 전에 이미 105% |
| d07 | 30대 후반 가구 | 5,500,000 | 1,650,000 | 600,000 | within | 구매 후 86.5% |
| d08 | 30대 후반 가구 | 5,000,000 | 1,250,000 | 700,000 | within | 한도는 여유인데 비상금 0.4개월치 |
| d09 | 경계 | 2,800,000 | 700,000 | 0 | unavailable | **카드 없음** → 월 지출을 알 수 없음, 결제일 기본 14일 |
| d10 | 경계 | 2,600,000 | 600,000 | 400,000 | within | **세이브박스 없음** → 비상금 0 |
| d11 | 경계 | 3,400,000 | 900,000 | 700,000 | over | 30일에 80건 → Spring 의 최근 50건 제한에 걸림 |
| d12 | 경계 | — | — | 0 | unavailable | 계좌·카드 모두 없는 신규 가입 |

- 카드 거래는 개별 날짜·가맹점·금액만 무작위이고, **최근 30일 합계는 위 값과 정확히 같다** (건수도 같다).
- 투자·적금 이체(`정기 이체(적금·투자)`)는 5·3·2 의 생활비(5) 구역이 아니라서 고정지출에 넣지 않았다.
- 월급 직후 기준일이면 연결계좌 잔액이 크게 나온다 (월급이 들어왔고 투자 이체는 다음 날이라서). 현실적인 모양이지만 기준일마다 달라진다.
- 카드대금은 전월 사용분을 결제일에 계좌에서 출금하는 모양으로 넣었다.

### 가격 데이터

- 제품 3개 × 120일, 글은 하루 평균 1.2건. 로그 가격이 평균으로 돌아오는 AR(1) 흐름에 제품당 3번의 세일 구간(4~7일, 추가 8~15% 할인)과
  글마다 0~10% 개별 할인을 얹었다. **기준가(99,000 / 119,000 / 49,000원)와 변동 폭은 임의로 정한 값**이고 실제 시세가 아니다.
- 입력 실수 이상치를 제품당 2건 넣고(×10, ×0.1), 그 위에 `mark_price_outliers` 배치와 같은 규칙(제품별 IQR×1.5)으로 `is_outlier` 를
  채웠다. 큰 세일 구간의 낮은 가격도 울타리 밖이면 같이 표시된다 (배치가 실제로 그렇게 동작한다). 이 표시가 스토어의 실제 배치
  결과와 정확히 같다는 것을 테스트가 확인한다.

## 스키마의 출처와 한계

- **금융 DDL(`schema/finance_schema.sql`)은 JPA 엔티티에서 옮겼다.** 저장소에 이 DB 의 DDL 이 없다(`ddl-auto=none`). 운영 DB 의
  실제 인덱스·제약·기본값·컬럼 타입은 확인하지 못했다. 실제 DDL 을 받으면 이 파일과 비교해야 한다. 테스트가 엔티티의
  `@Column`/`@JoinColumn` 선언(컬럼 이름과 NOT NULL 여부)과 이 파일이 만드는 컬럼이 같은지 검사한다.
- 엔티티에 없는데 더한 것: 일반 `long` 컬럼(`accounts.user_id` 등)의 FK, 조회용 인덱스(`idx_demo_*`).
- **가격 DDL(`schema/crawl_items_schema.sql`)은 `PostgresCrawlStore` 가 만드는 것과 같다** (테스트가 컬럼 목록·타입·NULL 여부를 비교).
  스토어의 `CREATE TABLE IF NOT EXISTS` 와 충돌하지 않는다.
- `price_engine/sql/price_engine_mvp_v1.sql` 의 `raw_listing`/`price_observation` 등은 만들지 않았다 (현재 코드가 쓰지 않는다).

## 확인한 것 / 하지 않은 것

확인함 (`ai/tests/test_demo_db.py`, 임시 PostgreSQL 에 실제로 적재):

- 같은 입력이면 같은 SQL, 365일 어느 기준일에도 생성 가능(잔액이 음수가 되지 않음).
- 계좌 거래의 잔액 연쇄, 계좌 잔액 = 마지막 거래의 `after_balance`, 카드 거래의 `user_id` = 카드 주인, 저축 설정이 사용자 본인의
  연결계좌·세이브박스를 가리킴.
- 계좌 거래에서 읽은 소득·고정지출 + 카드 30일 지출 + 130,000원을 실제 5·3·2 규칙에 넣은 상태가 위 표의 기대 상태와 같음.
- d11 은 Spring 방식(최근 3개월, 50건)으로 자르면 XAI 의 `estimate_monthly_spending` 이 잘림을 표시하고, 그 값으로 계산하면
  실제로는 `over` 인 사용자가 `within` 으로 판정됨 (아래 관찰 참고).
- 두 번 적재해도 데모 행이 중복되지 않음, `unload` 가 데모 행만 지움, 안전장치가 원격 호스트를 거부함.
- 가격 데이터가 기존 `build_price_feature_snapshot_v1` 을 통과하고, 17개 feature 중 12개가 값이 변함 (실제 크롤 67행은 0개).
  단 이 숫자는 이 테스트 안의 최소 변환(제품=`item_family`, 판매처=제목의 `[몰]`)에서 나온 것이다.

**Spring 까지 실제로 돌린 결과** (PostgreSQL 16 + Redis + AI 서버(uvicorn) + Spring jar, 모두 로컬, 외부 호출 없음):

- 데모 사용자 12명이 `demo-pass-1234` 로 로그인해 구매 PR 을 올리고 3개 품목을 평가했다 — 36건 모두 200.
  Spring 이 보낸 요청을 중간에서 받아 보니 월 소득·고정지출(`isEstimated`)이 시드의 정답과 11명 모두 정확히 같았고(계좌가 없는
  d12 는 보내지 않음), 월 지출(`monthlySpending30d`)은 DB 합계라 80건을 쓴 d11 도 시드의 700,000원과 같았다.
- 결과 (MX Master 3S 130,000원 기준): 한도 안(d01·d03·d05·d08)은 `BUY_NOW`, 빠듯함(d02)은 `WAIT`, 한도 초과(d04·d06·d11)는 `NOT_RECOMMENDED`, 한도 안이어도 d07 은 카드 결제일이 가깝고 구매 후 세이브박스 잔액이 얇아 `WAIT`, d10 은 비상금이 없어 `NOT_RECOMMENDED`,
  입력을 믿을 수 없는 경우(d09 카드 없음, d12 금융 정보 없음)는 `REVIEW`/`WAIT`. 예전에는 36건 중 `BUY_NOW` 가 0건이었다.
- 새 사용자가 계좌 개설 → 세이브박스 → 저축 규칙 → 모의 입금(자동저축) → 수동 저축/꺼내기 → 카드 등록·결제 입력을 거치고,
  주계좌+세이브박스 합계와 거래 내역 재계산이 맞는지, 남의 계좌·카드가 막히는지 확인했다.
- 같은 사용자에게 입금·저축·꺼내기 70건을 동시에 보내도 교착·5xx 없이 돈이 보존되고 자동저축이 입금마다 정확히 한 번 실행된다.
  구매 평가 48건 동시 호출도 모두 같은 판단이고 가격 이력 조회 실패가 없다.

돌릴 때 알아둘 것: 이 demo 스키마는 금융 테이블만 만든다. PR 작성·평가를 보려면 커뮤니티 테이블(`boards`, `posts`, `pr_posts` …)이
필요한데 저장소에 DDL 이 없다(`ddl-auto=none`). 한 번만 `SPRING_JPA_HIBERNATE_DDL_AUTO=update` 로 Spring 을 띄워 나머지 테이블을
만들고, `boards` 에 `category='PR'` 행을 하나 넣었다. 돈과 카드는 `FINANCE_MOCK_DATA_ENABLED=true` 일 때만 API 로 넣을 수 있다.

**확인하지 못함:**

- `docker compose` 연동은 만들지도 시험하지도 않았다. 컨테이너로 띄우려면 `postgres:16` 의
  `/docker-entrypoint-initdb.d` 에 `schema/*.sql` 과 `demo.py generate` 결과를 마운트하면 되지만, 직접 해 보지 않았다.
- 가격 모델을 이 데이터로 학습하지 않았다. 학습해도 의미 있는 검증이 아니다 (위 안내), 그리고 아래 설계 문제는 데이터와 무관하게 남는다.

## 이 작업 중에 알게 된 것 (Spring/AI 쪽 사실)

1. **Spring DB 에 월 소득·고정지출 열이 없다.** 5·3·2 예산 규칙은 이 두 값이 있어야 켜진다. 이제 Spring 이 입출금 계좌 거래의
   최근 3개월(이번 달 제외) 중앙값으로 추정해 `isEstimated` 로 보낸다(`MonthlyBudgetBasisEstimator`). 근거가 없으면 보내지 않는다.
   다만 추정이므로, 사용자에게 직접 입력받을지는 여전히 정해야 한다.
2. **`current_balance` 에 세이브박스가 포함된다.** `sumBalanceByUserId` 는 모든 계좌(세이브박스 포함)의 합이고,
   `emergency_fund_balance` 와 `savebox_balance` 는 보통 같은 세이브박스 잔액이다 (`resolveSaveboxBalance` 가 비상금으로 대체하기도 한다).
   재무 모델의 두 입력이 운영에서는 같은 값일 가능성이 높다 — 합성 학습 데이터의 상관(0.95~0.998)과 같은 방향의 문제다.
3. **(해결) 최근 50건 제한이 예산 판단을 뒤집을 수 있었다.** 이제 Spring 이 최근 30일 카드 지출 합계를 SQL 로 계산해
   `monthlySpending30d` 로 보내고 AI 는 그 값을 그대로 쓴다(거래 목록은 합계를 보내지 못한 호출자용 대체 경로로만 남는다).
4. 카드 거래가 없으면 `days_until_card_due` 는 14일 기본값이 `isDefault` 표시 없이 들어간다 (`FinanceProfileService` 의 `orElse(14)`).
