from __future__ import annotations

from typing import Any


class CounterfactualEngine:
    def suggest(
        self,
        *,
        price_int: int | None,
        monthly_spending_30d: float,
        emergency_fund_balance: float,
        current_balance: float,
        days_until_card_due: int,
        expected_card_payment_amount: float,
    ) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []
        price_value = float(price_int) if price_int is not None else 0.0

        if emergency_fund_balance < (monthly_spending_30d * 0.5):
            target = int((monthly_spending_30d * 0.5) - emergency_fund_balance)
            suggestions.append(
                {
                    "type": "dice_style",
                    "feature": "emergency_fund_balance",
                    "action": "increase",
                    "suggested_change": max(target, 0),
                    "message": f"비상자금을 약 {max(target, 0):,}원 늘리면 구매 리스크가 완화될 수 있습니다.",
                }
            )

        projected = current_balance - price_value
        safe_balance = monthly_spending_30d * 0.15
        if projected < safe_balance and price_value > 0:
            gap = int(safe_balance - projected)
            suggestions.append(
                {
                    "type": "dice_style",
                    "feature": "current_price",
                    "action": "decrease",
                    "suggested_change": max(gap, 0),
                    "message": f"가격이 약 {max(gap, 0):,}원 낮아지거나 잔액이 늘어나면 판단이 개선될 수 있습니다.",
                }
            )

        if days_until_card_due < 7 and expected_card_payment_amount > (current_balance * 0.4):
            suggestions.append(
                {
                    "type": "dice_style",
                    "feature": "days_until_card_due",
                    "action": "delay_purchase",
                    "suggested_change": 7,
                    "message": "카드 결제일 이후로 구매 시점을 미루면 현금흐름 부담이 줄어듭니다.",
                }
            )

        if len(suggestions) == 0:
            suggestions.append(
                {
                    "type": "dice_style",
                    "feature": "current_price",
                    "action": "wait_for_better_price",
                    "suggested_change": 0,
                    "message": "가격 하락 또는 잔액 증가 시 재평가를 권장합니다.",
                }
            )

        return suggestions[:3]
