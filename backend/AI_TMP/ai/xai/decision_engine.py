from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .budget_rule import BudgetStatus, status_from_ratios


@dataclass(frozen=True)
class DecisionOutcome:
    final_decision: str
    decision_confidence: float
    fired_rule_ids: list[str]


class DecisionEngine:
    RULE_VERSION = "financial-purchase-copilot-xai-rules-v1"

    # 입력이 믿을 만하지 않을 때 '지금 구매'를 막고 대신 내리는 판단.
    BLOCKED_BUY_RULE_ID = "BUY_BLOCKED_UNRELIABLE_INPUT"

    def decide(
        self, feature_scores: dict[str, Any], *, inputs_reliable: bool = True
    ) -> DecisionOutcome:
        """구매 판단.

        inputs_reliable=False 는 재무 모델 입력이 기본값이거나 월 지출이 일부만 집계된(하한값) 경우다.
        그 값으로는 '여유가 있다'를 증명할 수 없으므로 BUY_NOW 를 막고 REVIEW 로 내린다.
        (비추천/관망은 그대로 둔다 — 부족한 정보가 '사도 된다'는 쪽으로만 틀리게 하지 않는다.)
        """
        outcome = self._decide_core(feature_scores)
        if outcome.final_decision == "BUY_NOW" and not inputs_reliable:
            return DecisionOutcome(
                final_decision="REVIEW",
                decision_confidence=min(outcome.decision_confidence, 0.5),
                fired_rule_ids=[*outcome.fired_rule_ids, self.BLOCKED_BUY_RULE_ID],
            )
        return outcome

    def _decide_core(self, feature_scores: dict[str, Any]) -> DecisionOutcome:
        current_price = float(feature_scores.get("current_price", 0.0))
        relative_price = float(feature_scores.get("avg_price_30d", 0.0))
        model_price_gap = float(feature_scores.get("price_model_gap_score", 0.0))
        price_signal = current_price + relative_price + (model_price_gap * 0.5)

        # 5·3·2 예산 규칙 (앞단이 소득/고정지출을 보냈을 때만 점수표에 키가 있다).
        # 생활비 5 구역을 넘기는 구매는 다른 신호와 상관없이 권하지 않는다.
        budget_status = self._budget_status(feature_scores)
        if budget_status == BudgetStatus.ALREADY_OVER:
            return DecisionOutcome(
                final_decision="NOT_RECOMMENDED",
                decision_confidence=self._clamp_confidence(
                    0.7 + (float(feature_scores["budget_ratio_before"]) - 1.0)
                ),
                fired_rule_ids=["BUDGET_ZONE_ALREADY_EXCEEDED"],
            )
        if budget_status == BudgetStatus.OVER:
            return DecisionOutcome(
                final_decision="NOT_RECOMMENDED",
                decision_confidence=self._clamp_confidence(
                    0.6 + (float(feature_scores["budget_ratio_after"]) - 1.0)
                ),
                fired_rule_ids=["BUDGET_ZONE_EXCEEDED"],
            )

        has_finance_model_signal = (
            "finance_model_risk_score" in feature_scores
            or "finance_model_affordability_score" in feature_scores
        )

        # 더 심각한 판정(비추천)을 덜 심각한 판정(관망)이 덮어쓰면 가격이 오를수록 판단이 좋아지는
        # 구간이 생긴다. 그래서 예산이 '빠듯함'이어도 재무 위험 검사를 먼저 하고, 그 뒤에 관망을 낸다.
        severe = self._severe_finance_outcome(feature_scores, has_finance_model_signal)
        if severe is not None:
            return severe

        if budget_status == BudgetStatus.TIGHT:
            return DecisionOutcome(
                final_decision="WAIT",
                decision_confidence=self._clamp_confidence(
                    0.5 + (float(feature_scores["budget_ratio_after"]) - 0.9) * 2.0
                ),
                fired_rule_ids=["BUDGET_ZONE_NEARLY_FULL"],
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

        if price_signal >= 1.2 and finance_model_affordability >= 0.1:
            confidence = self._clamp_confidence(
                (price_signal * 0.6) + (finance_model_affordability * 0.4)
            )
            return DecisionOutcome(
                final_decision="BUY_NOW",
                decision_confidence=confidence,
                fired_rule_ids=["PRICE_FAVORABLE_AND_FINANCE_MODEL_AFFORDABLE"],
            )

        # 예산 한도 안에서 여유가 있고, 재무 모델도 안전하며, 결제일이 임박하지 않으면 사도 된다.
        # (가격 모델이 없어도 이 규칙으로 '지금 사도 되는' 판단이 나올 수 있다.)
        if (
            budget_status == BudgetStatus.WITHIN
            and finance_model_risk < 0.3
            and finance_model_affordability >= 0.1
            and due_pressure >= 0.25
        ):
            return DecisionOutcome(
                final_decision="BUY_NOW",
                decision_confidence=self._clamp_confidence(
                    0.6 + (1.0 - float(feature_scores["budget_ratio_after"])) * 0.4
                ),
                fired_rule_ids=["BUDGET_WITHIN_AND_AFFORDABLE"],
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

    def _severe_finance_outcome(
        self, feature_scores: dict[str, Any], has_finance_model_signal: bool
    ) -> DecisionOutcome | None:
        """재무 상태만으로 '권하지 않는다'가 되는 경우. 해당하지 않으면 None."""
        if has_finance_model_signal:
            risk = float(feature_scores.get("finance_model_risk_score", 0.0))
            if risk >= 0.55:
                return DecisionOutcome(
                    final_decision="NOT_RECOMMENDED",
                    decision_confidence=self._clamp_confidence((risk - 0.55) * 2.0 + 0.6),
                    fired_rule_ids=["FINANCE_MODEL_HIGH_RISK"],
                )
            return None
        spend_pressure = float(feature_scores.get("product_price_vs_monthly_spending", 0.0))
        emergency_buffer = float(feature_scores.get("emergency_fund_balance", 0.0))
        projected_balance = float(feature_scores.get("projected_balance_after_purchase", 0.0))
        finance_stress = spend_pressure - emergency_buffer - projected_balance
        if finance_stress > 1.2:
            return DecisionOutcome(
                final_decision="NOT_RECOMMENDED",
                decision_confidence=self._clamp_confidence((finance_stress - 1.2) / 2.0),
                fired_rule_ids=["FIN_HIGH_STRESS"],
            )
        return None

    @staticmethod
    def _budget_status(feature_scores: dict[str, Any]) -> BudgetStatus | None:
        """점수표에 예산 사용률이 있으면 상태를, 없으면 None (예산 규칙을 적용하지 않는다)."""
        before = feature_scores.get("budget_ratio_before")
        after = feature_scores.get("budget_ratio_after")
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            return status_from_ratios(float(before), float(after))
        return None

    @staticmethod
    def _clamp_confidence(raw: float) -> float:
        return min(max(raw, 0.0), 1.0)
