"""'무엇을 바꾸면 구매 판단이 나아지나'를 실제 판단 경로로 검증해서 찾는다.

예전 DiCE 경로의 문제 (xai/dice_engine.py)
    - 대리모델이 실제 모델이 아니었다. 64행짜리 장난감 규칙(예산>=가격 그리고
      비상금>=30만)을 학습한 RandomForest 였다. 그래서 제안이 실제 판단과 무관했다.
    - 입력이 잘못 매핑됐다. 세이브박스 잔액이 비상자금과 현재 잔액 둘 다에 들어갔다.
    - 바꿀 수 없는 값(결제일 등)도 후보였고, 범위 제한이 없었다.
    - 서비스가 type 이 "dice" 이기만 하면 validated=True 로 표시했다. 확인한 적이
      없는데 확인했다고 말한 것이다.
    - 한 번 도는 데 수십 초가 걸렸다 (Spring 읽기 제한은 60초).

여기서 하는 일
    사용자가 실제로 바꿀 수 있는 값만 후보로 삼는다.
        - 상품 가격을 낮춘다 (싼 걸 고르거나 할인을 기다린다)
        - 비상자금 / 세이브박스 / 계좌 잔액을 늘린다
    (카드 결제일, 이미 나간 한 달 지출, 곧 나갈 카드 결제액은 바꿀 수 없다.)
    각 후보를 작은 변화부터 차례로 시도하며, 매번 실제 파이프라인(모델 + 규칙 엔진)을
    다시 돌려 결과를 확인한다. 판단이 지금보다 한 단계 이상 나아진 첫 변화만 제안한다.
    그래서 제안에는 '확인된 결과'가 붙고, validated 는 사실이다.

    이 엔진은 모델/규칙을 직접 알지 못한다. evaluate 함수만 받는다. 서비스가 실제
    경로를 evaluate 로 꽂는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

DECISION_RANK: dict[str, int] = {
    "NOT_RECOMMENDED": 0,
    "WAIT": 1,
    "REVIEW": 2,
    "BUY_NOW": 3,
}

_DECISION_LABEL_KO: dict[str, str] = {
    "BUY_NOW": "바로 구매",
    "REVIEW": "재검토",
    "WAIT": "대기",
}

# 사용자가 바꿀 수 있는 값. (시나리오 키, 방향, 조사까지 붙은 한국어 이름)
LEVERS: tuple[tuple[str, str, str], ...] = (
    ("emergency_fund_balance", "increase", "비상자금을"),
    ("savebox_balance", "increase", "세이브박스 잔액을"),
    ("current_balance", "increase", "계좌 잔액을"),
    ("product_price", "decrease", "가격이"),
)
ACTIONABLE_KEYS: frozenset[str] = frozenset(key for key, _, _ in LEVERS)

_MONEY_UNIT = 10_000  # 잔액 제안은 만 원 단위
_PRICE_UNIT = 1_000  # 가격 제안은 천 원 단위

# 잔액을 월 지출의 몇 배까지 늘려 볼지: (상한 배수, 간격 배수) 구간들.
_BALANCE_GRID_SEGMENTS: tuple[tuple[float, float], ...] = (
    (0.2, 0.02),
    (1.0, 0.05),
    (3.0, 0.10),
)
_PRICE_DISCOUNT_STEP = 0.05
_PRICE_DISCOUNT_MAX = 0.90


@dataclass(frozen=True)
class Outcome:
    decision: str
    finance_risk_score: float | None = None


Evaluate = Callable[[Mapping[str, float]], Outcome]


def _round_down(value: float, unit: int) -> int:
    return int(value // unit) * unit


def _round_up(value: float, unit: int) -> int:
    return int(-(-value // unit)) * unit


def _balance_deltas(monthly_spending: float) -> list[int]:
    """작은 변화부터 큰 변화까지 만 원 단위로 중복 없이."""
    base = max(float(monthly_spending), 1.0)
    deltas: list[int] = []
    start = 0.0
    for limit, step in _BALANCE_GRID_SEGMENTS:
        multiple = start + step
        while multiple <= limit + 1e-9:
            delta = max(_round_up(base * multiple, _MONEY_UNIT), _MONEY_UNIT)
            if not deltas or delta > deltas[-1]:
                deltas.append(delta)
            multiple += step
        start = limit
    return deltas


def _price_candidates(price: float) -> list[int]:
    candidates: list[int] = []
    discount = _PRICE_DISCOUNT_STEP
    while discount <= _PRICE_DISCOUNT_MAX + 1e-9:
        new_price = _round_down(price * (1.0 - discount), _PRICE_UNIT)
        if 0 < new_price < price and (not candidates or new_price < candidates[-1]):
            candidates.append(new_price)
        discount += _PRICE_DISCOUNT_STEP
    return candidates


class ModelCounterfactualEngine:
    def __init__(self, evaluate: Evaluate, *, max_results: int = 3) -> None:
        self._evaluate = evaluate
        self._max_results = max_results

    def suggest(
        self,
        *,
        current_decision: str,
        price: float,
        monthly_spending: float,
        current_values: Mapping[str, float],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """확인된 제안과 상태를 돌려준다. 확인되지 않은 제안은 절대 내지 않는다."""
        if current_decision not in DECISION_RANK:
            return [], {"enabled": False, "backend": "model_search", "reason": "unknown_decision"}
        if current_decision == "BUY_NOW":
            return [], {"enabled": True, "backend": "model_search", "count": 0, "reason": "already_buy_now"}

        # 목표는 '지금보다 한 단계 이상 나아진 판단'이다. 결제일 임박처럼 바꿀 수 없는 요인이
        # 있으면 '바로 구매'는 어떤 변화로도 안 나온다. 그럴 때 억지로 높은 목표를 세우면
        # 제안이 하나도 없게 된다. 도달한 판단은 제안에 그대로 적어 사용자가 직접 본다.
        target_rank = DECISION_RANK[current_decision] + 1
        monthly = max(float(monthly_spending), 1.0)

        found: list[dict[str, Any]] = []
        evaluations = 0
        for key, action, label in LEVERS:
            if key == "product_price":
                trials = [(float(v), float(price) - float(v)) for v in _price_candidates(price)]
            else:
                base = float(current_values.get(key, 0.0))
                trials = [(base + d, float(d)) for d in _balance_deltas(monthly)]

            for new_value, delta in trials:
                outcome = self._evaluate({key: float(new_value)})
                evaluations += 1
                if DECISION_RANK.get(outcome.decision, -1) >= target_rank:
                    found.append(
                        self._suggestion(
                            key=key,
                            action=action,
                            label=label,
                            delta=int(delta),
                            new_value=int(new_value),
                            outcome=outcome,
                            monthly=monthly,
                        )
                    )
                    break

        found.sort(key=lambda s: (s["relative_cost"], s["variable"]))
        results = found[: self._max_results]
        state: dict[str, Any] = {
            "enabled": True,
            "backend": "model_search",
            "count": len(results),
            "evaluations": evaluations,
        }
        if not results:
            state["reason"] = "no_single_change_found"
        return results, state

    @staticmethod
    def _suggestion(
        *,
        key: str,
        action: str,
        label: str,
        delta: int,
        new_value: int,
        outcome: Outcome,
        monthly: float,
    ) -> dict[str, Any]:
        result_label = _DECISION_LABEL_KO.get(outcome.decision, outcome.decision)
        if key == "product_price":
            message = (
                f"가격이 약 {delta:,}원 낮아져 {new_value:,}원 이하가 되면 "
                f"구매 판단이 '{result_label}'로 바뀝니다."
            )
        else:
            message = (
                f"{label} 약 {delta:,}원 늘려 {new_value:,}원이 되면 "
                f"구매 판단이 '{result_label}'로 바뀝니다."
            )
        return {
            "type": "model_search",
            "variable": key,
            "action": action,
            "suggested_change": delta,
            "threshold": float(new_value),
            "message": message,
            "validated": True,
            "target_decision": outcome.decision,
            "finance_risk_score_after": outcome.finance_risk_score,
            "relative_cost": delta / monthly,
        }
