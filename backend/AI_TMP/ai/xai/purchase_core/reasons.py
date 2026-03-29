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
}

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


def build_reason_item(feature: str, score: float) -> ReasonItem | None:
    if feature not in REASON_CODE_MAP:
        return None

    reason_code, source_type = REASON_CODE_MAP[feature]
    return ReasonItem(
        reason_code=reason_code,
        reason_text=REASON_TEXT[reason_code],
        feature=feature,
        score=float(score),
        source_type=source_type,
    )


def extract_top_reasons(
    feature_scores: Mapping[str, Any],
    top_k: int = 3,
) -> list[ReasonItem]:
    ranked_pairs = rank_reason_features(feature_scores, top_k=top_k)
    reasons: list[ReasonItem] = []
    for feature, score in ranked_pairs:
        reason = build_reason_item(feature, score)
        if reason is not None:
            reasons.append(reason)
    return reasons
