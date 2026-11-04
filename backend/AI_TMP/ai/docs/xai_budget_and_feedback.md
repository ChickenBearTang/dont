# 5·3·2 예산 규칙과 사용자 반응 수집

가격 모델에는 '좋은 가격'의 정답이 없다. 사용자 반응(좋았다/별로였다)이 쌓이기 전까지는 구매가 사용자
형편에 맞는지를 5·3·2 예산 규칙으로 본다. 이 문서는 (1) 그 규칙의 정의와 가정, (2) Spring 에 요청하는
입력, (3) 사용자 반응 수집 계약, (4) 아직 모르는 것을 적는다.

## 1. 5·3·2 예산 규칙

소득을 생활비 5 / 투자 3 / 저축 2 로 나눈다. **물건 가격은 생활비 5 구역에서 나가는 돈으로 본다**
(3 은 투자 영역이라 구매에 쓰지 않는다). 고정지출과 비상금 적립은 5 구역에 이미 들어 있다.

| 항목 | 정의 |
|---|---|
| 한도 | 월 소득 × 0.5 |
| 사용량 | 월 고정지출(비상금 적립 포함) + 최근 30일 변동 지출 |
| 구매 후 사용률 | (사용량 + 가격) ÷ 한도 |

| 상태 | 조건 | 결정 | 규칙 ID |
|---|---|---|---|
| `within` 여유 있음 | 구매 후 사용률 ≤ 90% | (아래 참고) | `BUDGET_WITHIN_AND_AFFORDABLE` |
| `tight` 빠듯함 | 90% 초과 ~ 100% | `WAIT` | `BUDGET_ZONE_NEARLY_FULL` |
| `over` 한도 초과 | 100% 초과 | `NOT_RECOMMENDED` | `BUDGET_ZONE_EXCEEDED` |
| `already_over` 이미 초과 | 구매 전 사용률이 이미 100% 초과 | `NOT_RECOMMENDED` | `BUDGET_ZONE_ALREADY_EXCEEDED` |
| `unavailable` 판단 안 함 | 소득/고정지출/월 지출 중 하나라도 앞단이 안 보냄 | 예산 규칙 미적용 (예전 동작) | — |

- 예산 규칙은 재무 모델과 가격 신호보다 **먼저** 평가한다. 한도를 넘는 구매는 다른 신호가 좋아도 권하지 않는다.
- `within` 이면 바로 `BUY_NOW` 가 되지는 않는다. 재무 모델이 있고 위험 점수 < 0.3, 여유 점수 ≥ 0.1, 카드 결제일이
  임박하지 않을 때(`BUDGET_WITHIN_AND_AFFORDABLE`)만 `BUY_NOW` 다. 재무 모델이 없으면 예전 휴리스틱으로 돌아간다.
- 임계값(90%, 100%, 비상금 3개월)은 **판단값**이다. 사용자 반응이 쌓이면 근거를 보고 조정한다. 코드: `xai/budget_rule.py`.
- 설명(요인 목록)에는 `BUDGET_ZONE_USAGE` 가 top_k 와 별개로 한 줄 더해진다. 한도에 가까우면 맨 앞, 여유가 있으면 맨 뒤.
  문구는 점수 부호가 아니라 상태로 정한다 (`BUDGET_STATUS_REASON_TEXT`).
- 반사실("무엇을 바꾸면 되나")은 가격을 낮춰 예산 상태가 바뀌는 경우를 실제로 다시 계산해서 제안한다.
  이미 초과한 상태(`already_over`)는 가격을 낮춰도 해결되지 않으므로 제안이 나오지 않을 수 있다.

### 가정 (앞단이 지켜야 맞는 숫자가 나온다)

1. **변동 지출(카드 거래에서 계산)과 고정지출은 겹치지 않는다.** 월세/구독이 카드로 나가고 고정지출에도 들어
   있으면 이중으로 센다.
2. **고정지출에는 매달 적립하는 비상금을 포함해서 보낸다.**
3. **소득은 월 실수령(세후) 금액**이다. 불규칙 소득이면 최근 몇 달 평균 같은 대표값을 앞단이 정해 보낸다.
4. 최근 30일 지출은 Spring 이 보내는 최근 거래 **최대 50건**에서 계산한다. 50건에 닿으면 하한값이라
   `SPENDING_TRUNCATED` 와 `FINANCE_FIELD_ESTIMATED:monthly_spending_30d` 경고가 나온다. 실제 사용률은 더 높을 수 있다.

## 2. Spring 에 요청하는 입력

`financeProfile` 에 아래 두 필드를 **실제 값으로** 보내 달라. 지금은 보내지 않아서 예산 규칙이 꺼져 있다.

| 필드 | 뜻 | 단위 |
|---|---|---|
| `availableFixedIncome` | 월 소득(세후) | 원, 0 초과 |
| `availableFixedExpense` | 월 고정지출. 매달 적립하는 비상금 포함 | 원, 0 이상 |

- 모르는 값을 0 이나 임의의 숫자로 채워 보내지 말고 **필드를 빼거나 `isDefault: true`** 로 보낸다. 기본값으로 표시된
  값은 예산 판단에 쓰지 않는다 (`isDefault` 를 항상 false 로 보내면 우리가 구분할 수 없다).
- 두 값 중 하나라도 없으면 예산은 판단하지 않는다: `BUDGET_RULE_UNAVAILABLE:income_not_provided_by_upstream`,
  `...:fixed_expense_not_provided_by_upstream`, `...:spending_not_provided_by_upstream` 경고가 나온다.

### 응답 변화 (스키마는 그대로, 값만 늘고 줄어든다)

- `financialEvaluation.keyMetrics` 에 `budget_zone_limit`, `budget_zone_used_before`, `budget_zone_used_after` 추가
  (예: `"1,600,000원 (107%)"`). 판단 안 함이면 추가하지 않는다.
- 앞단이 보내지 않아 기본값으로 채워진 `available_fixed_income`(100만 원), `available_fixed_expense`(0원) 지표는
  **더 이상 보여주지 않는다**. 예전에는 기본값을 사실처럼 보여줬다. 쓰인 사실은 `FINANCE_FIELD_DEFAULTED:*` 경고로 남는다.
- `topFactors` 에 `BUDGET_ZONE_USAGE`, `warnings` 에 `BUDGET_RULE_UNAVAILABLE:*`, `EMERGENCY_COVER_LOW`
  (비상금이 사용량의 3개월 미만) 가 나올 수 있다. Spring DTO 가 `warnings` 와 `topFactors.code` 를 열거형으로
  제한하고 있다면 이 값들을 허용해야 한다.

## 3. 사용자 반응 수집 계약

```
POST /api/v1/xai/purchase-evaluations/{requestId}/feedback
```

```json
{
  "purchaseRequestId": 123,
  "aspect": "price",
  "verdict": "good",
  "action": "purchased",
  "reasons": ["PRICE_FAIR"],
  "comment": "생각보다 싸게 샀어요"
}
```

| 필드 | 값 | 비고 |
|---|---|---|
| `aspect` (필수) | `price` / `decision` / `explanation` | **무엇에 대한 반응인가.** 섞어 집계하면 라벨의 뜻이 흐려지므로 구분한다. 가격 모델의 정답 후보는 `price` 만이다. |
| `verdict` (필수) | `good` / `bad` | |
| `action` | `purchased` / `not_purchased` / `unknown`(기본) | 구매 여부에 따라 '좋았다'의 뜻이 달라진다. |
| `reasons` | `PRICE_TOO_HIGH`, `PRICE_FAIR`, `CHEAPER_ELSEWHERE`, `BUDGET_TOO_TIGHT`, `TOO_CAUTIOUS`, `TOO_PERMISSIVE`, `WRONG_PRODUCT`, `OTHER` | 최대 5개, 중복 제거 |
| `comment` | 최대 300자 | 개인정보를 쓰지 않도록 화면에서 안내한다. |
| `purchaseRequestId` (필수) | | 그 평가의 값과 같아야 한다. |

응답: `{requestId, purchaseRequestId, aspect, verdict, status, feedbackId}`

| status | 뜻 |
|---|---|
| `recorded` | 새로 기록 |
| `duplicate` | 같은 평가·같은 대상에 같은 내용이 이미 있음 (재전송해도 안전) |
| `changed` | 같은 평가·같은 대상에 의견을 바꿈. **마지막 값이 유효**하고 이전 기록은 지우지 않는다 |

| HTTP | 경우 |
|---|---|
| 404 `EVALUATION_NOT_FOUND` | 우리가 평가한 적 없는 requestId (감사 로그에 없음). 임의의 id 로 데이터가 오염되는 것을 막는다. XAI 랩의 모의 평가도 여기 해당한다. |
| 422 `PURCHASE_REQUEST_MISMATCH` | `purchaseRequestId` 가 그 평가의 값과 다름 |
| 422 | 본문 형식 오류 (모르는 필드 포함) |

저장: `data/xai_feedback.jsonl` (추가 전용). 현재 값은 `(requestId, aspect)` 별 마지막 줄이다
(`JsonlFeedbackStore.current_rows()`). 인증과 호출 빈도 제한은 이 서비스가 아니라 Spring 에서 건다
(이 서비스는 내부망 호출만 받는다고 가정한다).

### 입력 스냅샷 (기본 꺼짐)

반응을 학습 데이터로 쓰려면 '그때 입력이 무엇이었는지'가 필요하다. 감사 로그에는 입력 해시만 있어 복원할 수 없다.

- `AI_XAI_SNAPSHOT_ENABLED=1` 이면 평가마다 `data/xai_input_snapshots.jsonl` 에 한 줄을 남긴다:
  `requestId, purchaseRequestId, decision, price, financeProfile(숫자 8개), origins, budget, ruleVersion, modelVersion`.
- 상품명, 가맹점, 거래 내역은 저장하지 않는다 (허용 목록 `SNAPSHOT_FINANCE_FIELDS` 밖의 필드는 저장소가 버린다).
- **재무 정보는 개인정보다.** 켜기 전에 보관 기간, 접근 권한, 사용자 고지를 정해야 한다. 그래서 기본은 꺼짐이다.
- XAI 랩의 모의 평가는 감사 로그와 스냅샷에 남지 않는다.

## 4. 아직 모르는 것 / 하지 않은 것

- **이 반응으로 모델을 학습하거나 선택하는 코드는 없다.** 수집 계약과 저장만 있다.
- 반응은 이진(좋았다/별로였다)이라 재무 모델의 3단계 라벨(low/medium/high)과 바로 대응하지 않는다. 쓰려면
  "후회했는가" 같은 이진 라벨을 따로 정의해야 하고, 지금의 선택 관문(10만 건 이상의 *실제 라벨*)은 그 라벨 기준으로
  다시 정해야 한다.
- 반응이 편향될 수 있다: 구매한 사람만 반응하는지, 판단을 먼저 보고 반응하는지(앵커링), 불만족한 사람이 더 많이
  누르는지. `action` 과 `decision` 을 같이 저장하므로 분석할 때 나눠 볼 수 있지만 보정은 하지 않았다.
- 5·3·2 의 50% 한도와 90% 경계는 통념(5·3·2 저축법)과 판단에서 온 값이다. 한국 20~30대에게 맞다는 근거가 있는
  것이 아니다. 반응 데이터로 검증/조정해야 한다.
- 예산은 한 달 단위 단순 합이다. 연간 지출(보험, 세금), 일시 소득, 이미 계획된 큰 지출은 모른다.
