from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class _ReasonTemplate:
    code: str
    text: str
    source_type: str


class ReasoningEngine:
    _FEATURE_REASON_MAP: dict[str, _ReasonTemplate] = {
        "avg_price_30d": _ReasonTemplate(
            code="PRICE_RELATIVE_TO_30D_AVG",
            text="현재 가격이 최근 30일 평균가 대비 유리합니다.",
            source_type="price_signal",
        ),
        "current_price": _ReasonTemplate(
            code="PRICE_CURRENT_LEVEL",
            text="현재 절대 가격 수준이 판단에 영향을 주었습니다.",
            source_type="price_signal",
        ),
        "coupon_applied": _ReasonTemplate(
            code="PRICE_COUPON_DISCOUNT_APPLIED",
            text="쿠폰 할인으로 실질 구매 가격이 낮아졌습니다.",
            source_type="price_signal",
        ),
        "shipping_fee": _ReasonTemplate(
            code="PRICE_SHIPPING_COST_REDUCES_ATTRACTIVENESS",
            text="배송비가 전체 구매 매력도를 낮춥니다.",
            source_type="price_signal",
        ),
        "recent_30d_spending_growth_rate": _ReasonTemplate(
            code="FIN_RECENT_SPENDING_SURGE",
            text="최근 지출 증가로 예산 압박이 커진 상태입니다.",
            source_type="finance_signal",
        ),
        "emergency_fund_balance": _ReasonTemplate(
            code="FIN_EMERGENCY_BUFFER_TOO_LOW",
            text="비상자금 수준이 이번 구매 대비 낮습니다.",
            source_type="finance_signal",
        ),
        "projected_balance_after_purchase": _ReasonTemplate(
            code="FIN_BALANCE_AFTER_PURCHASE_TOO_LOW",
            text="구매 후 예상 잔액이 너무 낮아질 수 있습니다.",
            source_type="finance_signal",
        ),
        "product_price_vs_monthly_spending": _ReasonTemplate(
            code="FIN_PRICE_TOO_LARGE_VS_MONTHLY_SPENDING",
            text="상품 가격이 월 지출 규모 대비 높은 편입니다.",
            source_type="finance_signal",
        ),
        "days_until_card_due": _ReasonTemplate(
            code="TIME_CARD_DUE_SOON",
            text="카드 결제일이 임박해 현금흐름 부담이 큽니다.",
            source_type="finance_signal",
        ),
    }

    _UNKNOWN_REASON_TEMPLATE = _ReasonTemplate(
        code="DECISION_FEATURE_SIGNAL",
        text="개별 특성 기여도가 추천 판단에 영향을 주었습니다.",
        source_type="feature_score",
    )

    _FALLBACK_REASON: dict[str, Any] = {
        "reason_code": "NO_VALID_FEATURE_SCORES",
        "reason_text": "유효한 숫자형 특성 점수가 없어 기본 판단 근거를 사용했습니다.",
        "feature": None,
        "score": 0.0,
        "source_type": "fallback",
    }

    def analyze(
        self, feature_scores: dict[str, Any], top_k: int
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        if not isinstance(feature_scores, dict) or len(feature_scores) == 0:
            return [self._FALLBACK_REASON.copy()]

        valid_pairs: list[tuple[str, float]] = []
        for feature, raw_score in feature_scores.items():
            try:
                numeric_score = float(raw_score)
            except (TypeError, ValueError):
                continue
            valid_pairs.append((feature, numeric_score))

        if len(valid_pairs) == 0:
            return [self._FALLBACK_REASON.copy()]

        reasons = [self._build_reason(feature, score) for feature, score in valid_pairs]
        reasons.sort(
            key=lambda reason: (
                -abs(float(reason["score"])),
                str(reason["reason_code"]),
                str(reason["feature"]),
            )
        )
        return reasons[:top_k]

    def _build_reason(self, feature: str, score: float) -> dict[str, Any]:
        template = self._FEATURE_REASON_MAP.get(feature, self._UNKNOWN_REASON_TEMPLATE)
        return {
            "reason_code": template.code,
            "reason_text": template.text,
            "feature": feature,
            "score": float(score),
            "abs_score": abs(float(score)),
            "impact_direction": "positive" if score >= 0 else "negative",
            "shap_like_value": float(score),
            "source_type": template.source_type,
        }
