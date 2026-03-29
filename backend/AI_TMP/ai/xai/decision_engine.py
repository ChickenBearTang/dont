from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionOutcome:
    final_decision: str
    decision_confidence: float
    fired_rule_ids: list[str]


class DecisionEngine:
    RULE_VERSION = "financial-purchase-copilot-xai-rules-v1"

    def decide(self, feature_scores: dict[str, Any]) -> DecisionOutcome:
        current_price = float(feature_scores.get("current_price", 0.0))
        relative_price = float(feature_scores.get("avg_price_30d", 0.0))
        model_price_gap = float(feature_scores.get("price_model_gap_score", 0.0))
        price_signal = current_price + relative_price + (model_price_gap * 0.5)

        has_finance_model_signal = (
            "finance_model_risk_score" in feature_scores
            or "finance_model_affordability_score" in feature_scores
        )
        if not has_finance_model_signal:
            spend_pressure = float(
                feature_scores.get("product_price_vs_monthly_spending", 0.0)
            )
            emergency_buffer = float(feature_scores.get("emergency_fund_balance", 0.0))
            projected_balance = float(
                feature_scores.get("projected_balance_after_purchase", 0.0)
            )
            due_pressure = float(feature_scores.get("days_until_card_due", 0.0))
            finance_stress = spend_pressure - emergency_buffer - projected_balance

            if finance_stress > 1.2:
                confidence = self._clamp_confidence((finance_stress - 1.2) / 2.0)
                return DecisionOutcome(
                    final_decision="NOT_RECOMMENDED",
                    decision_confidence=confidence,
                    fired_rule_ids=["FIN_HIGH_STRESS"],
                )

            if price_signal >= 1.2 and finance_stress <= 0.2:
                confidence = self._clamp_confidence((price_signal - finance_stress) / 2.0)
                return DecisionOutcome(
                    final_decision="BUY_NOW",
                    decision_confidence=confidence,
                    fired_rule_ids=["PRICE_FAVORABLE_AND_AFFORDABLE"],
                )

            if due_pressure < 0.25:
                confidence = self._clamp_confidence((0.25 - due_pressure) + 0.3)
                return DecisionOutcome(
                    final_decision="WAIT",
                    decision_confidence=confidence,
                    fired_rule_ids=["TIME_NEAR_CARD_DUE_DATE"],
                )

            confidence = self._clamp_confidence(0.5 + abs(finance_stress) * 0.1)
            return DecisionOutcome(
                final_decision="REVIEW",
                decision_confidence=confidence,
                fired_rule_ids=["DECISION_REVIEW_REQUIRED"],
            )

        finance_model_risk = float(
            feature_scores.get("finance_model_risk_score", 0.0)
        )
        finance_model_affordability = float(
            feature_scores.get("finance_model_affordability_score", 0.0)
        )
        due_pressure = float(feature_scores.get("days_until_card_due", 0.0))

        if finance_model_risk >= 0.55:
            confidence = self._clamp_confidence((finance_model_risk - 0.55) * 2.0 + 0.6)
            return DecisionOutcome(
                final_decision="NOT_RECOMMENDED",
                decision_confidence=confidence,
                fired_rule_ids=["FINANCE_MODEL_HIGH_RISK"],
            )

        if price_signal >= 1.2 and finance_model_affordability >= 0.1:
            confidence = self._clamp_confidence(
                (price_signal * 0.6) + (finance_model_affordability * 0.4)
            )
            return DecisionOutcome(
                final_decision="BUY_NOW",
                decision_confidence=confidence,
                fired_rule_ids=["PRICE_FAVORABLE_AND_FINANCE_MODEL_AFFORDABLE"],
            )

        if due_pressure < 0.25 or finance_model_risk >= 0.3:
            confidence = self._clamp_confidence(
                max(0.25 - due_pressure, 0.0) + max(finance_model_risk, 0.0) + 0.25
            )
            return DecisionOutcome(
                final_decision="WAIT",
                decision_confidence=confidence,
                fired_rule_ids=["FINANCE_MODEL_CAUTION_OR_DUE_DATE"],
            )

        confidence = self._clamp_confidence(0.5 + abs(finance_model_risk) * 0.25)
        return DecisionOutcome(
            final_decision="REVIEW",
            decision_confidence=confidence,
            fired_rule_ids=["DECISION_REVIEW_REQUIRED"],
        )

    @staticmethod
    def _clamp_confidence(raw: float) -> float:
        return min(max(raw, 0.0), 1.0)
