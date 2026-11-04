"""5·3·2 예산 규칙: 이번 구매가 생활비(5) 구역을 넘기지 않는가.

소득을 생활비 5 / 투자 3 / 저축 2 로 나눈다. 물건 가격은 생활비 5 구역에서 나가는 돈으로 본다
(3 은 투자 영역). 가격 모델은 '좋은 가격'의 정답이 없어서 쓸 수 없고, 사용자 반응(좋았다/별로였다)
이 쌓이기 전까지는 이 규칙이 구매가 사용자 형편에 맞는지의 기준이다.

정의
    한도        = 월 소득 x 0.5
    사용량      = 고정지출 + 최근 30일 변동 지출
    사용률(후)  = (사용량 + 가격) / 한도
고정지출에는 매달 적립하는 비상금을 포함해서 받는다 ('고정지출과 비상금을 포함한 5 구역').

가정 (앞단이 지켜야 맞다)
    - 변동 지출(카드 거래에서 계산)과 고정지출은 겹치지 않는다. 월세/구독이 카드로 나가고
      고정지출에도 들어 있으면 이중으로 센다.
    - 소득과 고정지출은 앞단이 실제 값을 보낸다. 기본값으로 채운 값은 호출하는 쪽에서 None 으로 바꿔
      넘기고, 여기서는 None 이면 '판단 불가'다 (추측하지 않는다).

임계값(TIGHT_RATIO 등)은 판단값이다. 사용자 반응 데이터가 쌓이면 근거를 보고 조정한다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import math
from typing import Any

ZONE_NEEDS_SHARE = 0.5  # 생활비
ZONE_INVEST_SHARE = 0.3  # 투자
ZONE_SAVINGS_SHARE = 0.2  # 저축

TIGHT_RATIO = 0.9  # 구매 후 사용률이 이 값을 넘으면 '빠듯함'
OVER_RATIO = 1.0
SCORE_SCALE = 0.3  # 사용률이 1.0 에서 이만큼 벗어나면 점수가 ±1 에 닿는다
EMERGENCY_COVER_TARGET_MONTHS = 3.0


class BudgetStatus(str, Enum):
    WITHIN = "within"  # 구매 후에도 한도 안에서 여유 있음
    TIGHT = "tight"  # 한도 안이지만 빠듯함 (한도의 90% 초과 ~ 100%)
    OVER = "over"  # 이번 구매로 한도를 넘음
    ALREADY_OVER = "already_over"  # 구매 전에 이미 한도를 넘음
    UNAVAILABLE = "unavailable"  # 입력이 없어 판단하지 않음


@dataclass(frozen=True)
class BudgetAssessment:
    status: BudgetStatus
    reason: str | None = None
    income: float | None = None
    limit: float | None = None
    fixed_expense: float | None = None
    variable_spending: float | None = None
    used_before: float | None = None
    used_after: float | None = None
    ratio_before: float | None = None
    ratio_after: float | None = None
    headroom_before: float | None = None
    headroom_after: float | None = None
    overshoot: float | None = None
    emergency_cover_months: float | None = None
    score: float | None = None  # 구매 유리도 (-1~1). 양수 = 한도 안에서 여유

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def status_from_ratios(ratio_before: float, ratio_after: float) -> BudgetStatus:
    if ratio_before > OVER_RATIO:
        return BudgetStatus.ALREADY_OVER
    if ratio_after > OVER_RATIO:
        return BudgetStatus.OVER
    if ratio_after > TIGHT_RATIO:
        return BudgetStatus.TIGHT
    return BudgetStatus.WITHIN


def score_from_ratio(ratio_after: float) -> float:
    """구매 후 사용률 -> 구매 유리도. 1.0(한도)에서 0, 낮을수록 +, 높을수록 -."""
    return max(-1.0, min(1.0, (OVER_RATIO - ratio_after) / SCORE_SCALE))


# 설명용 점수. 규칙 판단과 같은 방향을 말하도록 상태로 부호를 정한다.
TIGHT_EXPLANATION_SCORE = -0.1
OVER_EXPLANATION_FLOOR = -0.3
ALREADY_OVER_EXPLANATION_FLOOR = -0.5


def explanation_score(assessment: "BudgetAssessment") -> float | None:
    """설명(요인 목록)에 쓰는 '구매에 유리한 정도'. 판단 불가면 None.

    score 자체는 사용률만 보므로 빠듯함(0.9~1.0)에서도 양수가 나온다. 하지만 규칙은 그 구간을
    WAIT 로 보므로, 설명에는 상태에 맞는 부호와 최소 크기를 준다 (한도 초과는 항상 눈에 띄게).
    """
    if assessment.status is BudgetStatus.UNAVAILABLE or assessment.score is None:
        return None
    if assessment.status is BudgetStatus.WITHIN:
        return assessment.score  # 사용률 0.9 이하라 항상 +0.33 이상
    if assessment.status is BudgetStatus.TIGHT:
        return TIGHT_EXPLANATION_SCORE
    if assessment.status is BudgetStatus.OVER:
        return min(assessment.score, OVER_EXPLANATION_FLOOR)
    return min(assessment.score, ALREADY_OVER_EXPLANATION_FLOOR)


def _unavailable(reason: str) -> BudgetAssessment:
    return BudgetAssessment(status=BudgetStatus.UNAVAILABLE, reason=reason)


def assess_budget(
    *,
    monthly_income: object,
    fixed_expense: object,
    variable_spending_30d: object,
    price: object,
    emergency_fund_balance: object = None,
) -> BudgetAssessment:
    income = _number(monthly_income)
    if income is None or income <= 0:
        return _unavailable("income_unknown_or_not_positive")
    fixed = _number(fixed_expense)
    if fixed is None:
        return _unavailable("fixed_expense_unknown")
    variable = _number(variable_spending_30d)
    if variable is None:
        return _unavailable("spending_unknown")
    purchase = _number(price)
    if purchase is None or purchase < 0:
        return _unavailable("price_invalid")

    fixed = max(fixed, 0.0)
    variable = max(variable, 0.0)
    limit = income * ZONE_NEEDS_SHARE
    used_before = fixed + variable
    used_after = used_before + purchase
    ratio_before = used_before / limit
    ratio_after = used_after / limit

    emergency = _number(emergency_fund_balance)
    cover = (emergency / used_before) if emergency is not None and emergency >= 0 and used_before > 0 else None

    return BudgetAssessment(
        status=status_from_ratios(ratio_before, ratio_after),
        income=income,
        limit=limit,
        fixed_expense=fixed,
        variable_spending=variable,
        used_before=used_before,
        used_after=used_after,
        ratio_before=ratio_before,
        ratio_after=ratio_after,
        headroom_before=limit - used_before,
        headroom_after=limit - used_after,
        overshoot=max(used_after - limit, 0.0),
        emergency_cover_months=cover,
        score=score_from_ratio(ratio_after),
    )
