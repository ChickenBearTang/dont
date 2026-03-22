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
            text="Current price is favorable relative to the 30-day average.",
            source_type="price_signal",
        ),
        "current_price": _ReasonTemplate(
            code="CURRENT_PRICE_LEVEL",
            text="Current absolute price level influenced the decision.",
            source_type="price_signal",
        ),
        "coupon_applied": _ReasonTemplate(
            code="COUPON_DISCOUNT_APPLIED",
            text="Coupon discount lowers the effective purchase price.",
            source_type="price_signal",
        ),
        "shipping_fee": _ReasonTemplate(
            code="SHIPPING_COST_REDUCES_ATTRACTIVENESS",
            text="Shipping cost reduces overall deal attractiveness.",
            source_type="price_signal",
        ),
        "recent_30d_spending_growth_rate": _ReasonTemplate(
            code="RECENT_SPENDING_SURGE",
            text="Recent spending growth indicates higher budget pressure.",
            source_type="finance_signal",
        ),
        "emergency_fund_balance": _ReasonTemplate(
            code="EMERGENCY_FUND_TOO_LOW",
            text="Emergency fund level appears low for this purchase.",
            source_type="finance_signal",
        ),
        "projected_balance_after_purchase": _ReasonTemplate(
            code="BALANCE_AFTER_PURCHASE_TOO_LOW",
            text="Projected post-purchase balance may become too low.",
            source_type="finance_signal",
        ),
        "product_price_vs_monthly_spending": _ReasonTemplate(
            code="PRICE_TOO_LARGE_VS_MONTHLY_SPENDING",
            text="Item price is high compared with monthly spending.",
            source_type="finance_signal",
        ),
        "days_until_card_due": _ReasonTemplate(
            code="CARD_DUE_SOON",
            text="Card payment due date is near, increasing cashflow pressure.",
            source_type="finance_signal",
        ),
    }

    _UNKNOWN_REASON_TEMPLATE = _ReasonTemplate(
        code="FEATURE_SIGNAL",
        text="Feature contribution influenced the recommendation.",
        source_type="feature_score",
    )

    _FALLBACK_REASON: dict[str, Any] = {
        "reason_code": "NO_VALID_FEATURE_SCORES",
        "reason_text": "No valid numeric feature scores were provided.",
        "feature": None,
        "score": 0.0,
        "source_type": "fallback",
    }

    def analyze(self, feature_scores: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
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
            "source_type": template.source_type,
        }
