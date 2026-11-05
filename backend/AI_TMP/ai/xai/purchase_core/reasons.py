from __future__ import annotations

from typing import Any, Mapping

from .contracts import ReasonItem

REASON_CODE_MAP: dict[str, tuple[str, str]] = {
    "avg_price_30d": ("PRICE_RELATIVE_TO_30D_AVG", "price_shap"),
    "current_price": ("CURRENT_PRICE_LEVEL", "price_shap"),
    "coupon_applied": ("COUPON_DISCOUNT_APPLIED", "price_shap"),
    "shipping_fee": ("SHIPPING_COST_REDUCES_ATTRACTIVENESS", "price_shap"),
    "recent_30d_spending_growth_rate": ("RECENT_SPENDING_SURGE", "finance_shap"),
    "emergency_fund_balance": ("EMERGENCY_FUND_TOO_LOW", "finance_shap"),
    "projected_balance_after_purchase": (
        "BALANCE_AFTER_PURCHASE_TOO_LOW",
        "finance_shap",
    ),
    "product_price_vs_monthly_spending": (
        "PRICE_TOO_LARGE_VS_MONTHLY_SPENDING",
        "finance_shap",
    ),
    "days_until_card_due": ("CARD_DUE_SOON", "finance_shap"),
    "price_model_gap_score": ("PRICE_MODEL_GAP_SIGNAL", "price_model"),
    "budget_zone_usage": ("BUDGET_ZONE_USAGE", "budget_rule"),
    "input_reliability": ("INPUT_UNRELIABLE", "input_quality"),
    "finance_model_risk_score": ("FINANCE_MODEL_HIGH_RISK_SIGNAL", "finance_model"),
    "finance_model_affordability_score": (
        "FINANCE_MODEL_AFFORDABILITY_SIGNAL",
        "finance_model",
    ),
}

REASON_TEXT: dict[str, str] = {
    "PRICE_RELATIVE_TO_30D_AVG": "현재 가격이 최근 30일 평균가 대비 높게 형성되어 있습니다.",
    "CURRENT_PRICE_LEVEL": "현재 가격 수준이 전체 판단에 중요한 영향을 주었습니다.",
    "COUPON_DISCOUNT_APPLIED": "쿠폰 할인 적용 여부가 가격 매력도에 반영되었습니다.",
    "SHIPPING_COST_REDUCES_ATTRACTIVENESS": "배송비 부담이 최종 가격 매력도를 낮췄습니다.",
    "RECENT_SPENDING_SURGE": "최근 소비 증가 흐름이 재무 부담 신호로 반영되었습니다.",
    "EMERGENCY_FUND_TOO_LOW": "비상자금 수준이 낮아 재무 안정성이 부족합니다.",
    "BALANCE_AFTER_PURCHASE_TOO_LOW": "구매 후 예상 잔액이 낮아질 가능성이 큽니다.",
    "PRICE_TOO_LARGE_VS_MONTHLY_SPENDING": "상품 가격이 월 지출 규모 대비 크게 느껴집니다.",
    "CARD_DUE_SOON": "카드 결제일이 가까워 단기 현금흐름 부담이 있습니다.",
    "BUDGET_ZONE_USAGE": "이번 구매가 생활비 구역(소득의 50%) 사용량에 영향을 주었습니다.",
}

# 예산 사유는 점수의 부호가 아니라 '상태'로 문구를 고른다. 점수 크기만으로는
# "빠듯함(한도의 90% 초과)"과 "여유 있음"이 같은 부호로 섞여 규칙 판단과 어긋난다.
BUDGET_STATUS_REASON_TEXT: dict[str, str] = {
    "within": "이번 구매 후에도 생활비 구역(소득의 50%) 안에서 여유가 있습니다.",
    "tight": "이번 구매 후 생활비 구역(소득의 50%)이 한도에 거의 찹니다.",
    "over": "이번 구매로 생활비 구역(소득의 50%)을 넘게 됩니다.",
    "already_over": "이번 달 생활비 구역(소득의 50%)을 이미 넘긴 상태입니다.",
}

# '지금 구매'를 막았을 때의 이유. 점수 부호가 아니라 원인(기본값 / 잘림)으로 문구를 고른다.
INPUT_UNRELIABLE_TEXT: dict[str, str] = {
    "default": "일부 재무 정보를 받지 못해 기본값으로 계산했어요. 확인되기 전에는 '지금 구매'로 판단하지 않아요.",
    "truncated": "최근 거래가 많아 월 지출이 일부만 집계됐어요(실제보다 작을 수 있어요). 그래서 '지금 구매'로 판단하지 않아요.",
}
REASON_TEXT["INPUT_UNRELIABLE"] = INPUT_UNRELIABLE_TEXT["default"]

REASON_TEXT.setdefault(
    "PRICE_MODEL_GAP_SIGNAL",
    "가격 모델 신호가 최종 판단에 영향을 주었습니다.",
)
REASON_TEXT.setdefault(
    "FINANCE_MODEL_HIGH_RISK_SIGNAL",
    "재무 모델이 현재 구매를 다소 높은 리스크로 평가했습니다.",
)
REASON_TEXT.setdefault(
    "FINANCE_MODEL_AFFORDABILITY_SIGNAL",
    "재무 모델이 현재 구매 가능 여력을 판단 근거로 반영했습니다.",
)


# signed=True 일 때 쓰는 방향별 문구. score 는 '구매에 유리한 정도'다.
#   (유리할 때, 불리할 때, 영향이 미미할 때)
# 불리할 때 문구는 예전 REASON_TEXT 와 같다. 예전에는 점수 부호와 상관없이 이 문구가
# 고정으로 나가서, 형편이 좋은 사용자에게도 "비상자금이 부족합니다"가 나왔다.
SIGNED_REASON_TEXT: dict[str, tuple[str, str, str]] = {
    "PRICE_RELATIVE_TO_30D_AVG": (
        "현재 가격이 최근 30일 평균가보다 낮아 유리합니다.",
        "현재 가격이 최근 30일 평균가 대비 높게 형성되어 있습니다.",
        "현재 가격은 최근 30일 평균가와 비슷해 판단에 큰 영향을 주지 않았습니다.",
    ),
    "PRICE_MODEL_GAP_SIGNAL": (
        "가격 모델이 예상하는 적정가보다 현재 가격이 낮습니다.",
        "가격 모델이 예상하는 적정가보다 현재 가격이 높습니다.",
        "현재 가격은 가격 모델의 적정가와 비슷해 판단에 큰 영향을 주지 않았습니다.",
    ),
    "EMERGENCY_FUND_TOO_LOW": (
        "비상자금이 충분해 재무 안정성이 높습니다.",
        "비상자금 수준이 낮아 재무 안정성이 부족합니다.",
        "비상자금 수준은 판단에 큰 영향을 주지 않았습니다.",
    ),
    "BALANCE_AFTER_PURCHASE_TOO_LOW": (
        "구매 후에도 남는 여유 자금이 충분합니다.",
        "구매 후 예상 잔액이 낮아질 가능성이 큽니다.",
        "구매 후 예상 잔액은 판단에 큰 영향을 주지 않았습니다.",
    ),
    "PRICE_TOO_LARGE_VS_MONTHLY_SPENDING": (
        "상품 가격이 월 지출 규모에 비해 부담스럽지 않습니다.",
        "상품 가격이 월 지출 규모 대비 크게 느껴집니다.",
        "상품 가격과 월 지출의 비율은 판단에 큰 영향을 주지 않았습니다.",
    ),
    "CARD_DUE_SOON": (
        "카드 결제 부담이 작아 단기 현금흐름에 여유가 있습니다.",
        "카드 결제일이 가까워 단기 현금흐름 부담이 있습니다.",
        "카드 결제 부담은 판단에 큰 영향을 주지 않았습니다.",
    ),
}

# |score| 가 이 값 이하면 방향을 말하지 않고 '영향 미미'로 표현한다.
SIGNED_NEUTRAL_BAND = 0.05


def rank_reason_features(
    feature_scores: Mapping[str, Any],
    top_k: int,
) -> list[tuple[str, float]]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    numeric_pairs: list[tuple[str, float]] = []
    for feature, raw_score in feature_scores.items():
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        numeric_pairs.append((feature, score))

    numeric_pairs.sort(
        key=lambda pair: (
            -abs(pair[1]),
            pair[0],
        )
    )
    return numeric_pairs[:top_k]


def _signed_text(reason_code: str, score: float) -> str:
    texts = SIGNED_REASON_TEXT.get(reason_code)
    if texts is None:
        return REASON_TEXT[reason_code]  # 방향을 말할 수 없는 항목
    favorable, unfavorable, neutral = texts
    if abs(score) <= SIGNED_NEUTRAL_BAND:
        return neutral
    return favorable if score > 0 else unfavorable


def build_reason_item(
    feature: str, score: float, *, signed: bool = False
) -> ReasonItem | None:
    """signed=True 면 score 를 '구매에 유리한 정도'로 보고 부호에 맞는 문구를 쓴다.

    signed=False(기본)는 부호의 뜻이 정해지지 않은 예전 점수용이라 문구를 바꾸지 않는다.
    """
    if feature not in REASON_CODE_MAP:
        return None

    reason_code, source_type = REASON_CODE_MAP[feature]
    return ReasonItem(
        reason_code=reason_code,
        reason_text=_signed_text(reason_code, float(score)) if signed else REASON_TEXT[reason_code],
        feature=feature,
        score=float(score),
        source_type=source_type,
    )


def extract_top_reasons(
    feature_scores: Mapping[str, Any],
    top_k: int = 3,
    *,
    signed: bool = False,
) -> list[ReasonItem]:
    ranked_pairs = rank_reason_features(feature_scores, top_k=top_k)
    reasons: list[ReasonItem] = []
    for feature, score in ranked_pairs:
        reason = build_reason_item(feature, score, signed=signed)
        if reason is not None:
            reasons.append(reason)
    return reasons
