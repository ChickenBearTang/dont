"""재무 모델의 합성 학습 데이터와 라벨 규칙.

주의: 이 데이터는 **가짜**다.
    입력은 난수로 만들고, 정답 라벨은 아래 rule_bucket() 이라는 손으로 쓴 규칙이
    붙인다. 따라서 이 데이터로 잰 점수(F1 등)는 모델의 '정확도'가 아니라
    '규칙을 얼마나 흉내 냈나'다. 규칙 자체가 실제 사용자에게 맞는지는 이 데이터로
    알 수 없다. 실제 결과 라벨이 생기기 전까지 점수를 정확도로 보고하지 않는다.

규칙 버전 v2 (finance-risk-rule-v2)
    v1 은 다섯 조건이었고 그중 하나가 `고정 수입 < 고정 지출` 이었다. 그런데
    Spring 은 고정 수입/지출을 보내지 않아 운영에서는 항상 기본값이었다. 모델
    입력을 Spring 이 실제로 보내는 값으로 줄이면서(원본 7개) 그 조건을 제거했다.
    나머지 네 조건의 임계값은 v1 과 같다.

generate_rows() 는 원본 7개와 파생 3개(features.py 로 계산), 그리고 비교 실험용으로
제거된 입력(고정 수입/지출)을 열로 함께 내보낸다. 라벨은 원본 7개에만 의존하므로
나머지 열은 라벨에 영향이 없다.
"""

from __future__ import annotations

from typing import Any, Mapping

from .allowlist import RAW_INPUT_NAMES, TARGET_NAME
from .features import derive_model_features

RULE_VERSION = "finance-risk-rule-v2"

# 라벨 규칙과 모델 입력이 공유하는 원본 7개는 allowlist.RAW_INPUT_NAMES 하나만 쓴다.
__all__ = ["RAW_INPUT_NAMES", "RULE_VERSION", "generate_rows", "rule_bucket"]


def rule_bucket(row: Mapping[str, Any]) -> str:
    """원본 7개 입력으로 위험 구간(low/medium/high)을 정한다."""
    monthly = float(row["monthly_spending_30d"])
    price = float(row["product_price"])
    savebox = float(row["savebox_balance"])
    emergency = float(row["emergency_fund_balance"])
    days = float(row["days_until_card_due"])
    card_payment = float(row["expected_card_payment_amount"])
    balance = float(row["current_balance"])

    score = 0.0
    if price / max(monthly, 1.0) > 0.30:
        score += 1.0
    if (savebox - price) < monthly * 0.12:
        score += 1.0
    if emergency < monthly * 0.45:
        score += 1.0
    if days <= 7 and card_payment > balance * 0.35:
        score += 1.0

    if score >= 3.0:
        return "high"
    if score >= 1.5:
        return "medium"
    return "low"


def generate_rows(*, row_count: int, seed: int) -> list[dict[str, Any]]:
    """합성 행을 만든다. 같은 (row_count, seed) 는 항상 같은 결과다."""
    import numpy as np

    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for _ in range(max(row_count, 1)):
        monthly = float(rng.uniform(700_000, 3_800_000))
        current_balance = float(rng.uniform(100_000, 4_500_000))
        emergency = float(rng.uniform(0, 4_000_000))
        card_payment = float(rng.uniform(0, 1_500_000))
        days = float(int(rng.integers(1, 31)))
        savebox = float(max(0.0, emergency * float(rng.uniform(0.5, 1.6))))
        fixed_expense = float(monthly * float(rng.uniform(0.25, 0.8)))
        fixed_income = float(monthly * float(rng.uniform(0.55, 1.6)))
        price = float(rng.uniform(20_000, 950_000))

        row: dict[str, Any] = {
            "current_balance": current_balance,
            "emergency_fund_balance": emergency,
            "savebox_balance": savebox,
            "expected_card_payment_amount": card_payment,
            "days_until_card_due": days,
            "monthly_spending_30d": monthly,
            "product_price": price,
        }
        # 파생 비율은 모델과 같은 함수(features.py)로 계산한다. 정의가 갈라지지 않는다.
        row.update(derive_model_features(row))
        # 아래는 모델 입력이 아니다. 입력 구성 비교 실험(옛 12개)에서만 쓴다.
        row["available_fixed_expense"] = fixed_expense
        row["available_fixed_income"] = fixed_income
        row[TARGET_NAME] = rule_bucket(row)
        rows.append(row)
    return rows
