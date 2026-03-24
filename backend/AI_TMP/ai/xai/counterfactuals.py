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
                    "type": "threshold",
                    "variable": "emergency_buffer",
                    "action": "increase",
                    "suggested_change": int(max(target, 0)),
                    "threshold": float(monthly_spending_30d * 0.5),
                    "message": f"비상자금을 약 {max(target, 0):,}원 늘리면 구매 리스크가 완화될 수 있습니다.",
                }
            )

        projected = current_balance - price_value
        safe_balance = monthly_spending_30d * 0.15
        if projected < safe_balance and price_value > 0:
            gap = int(safe_balance - projected)
            suggestions.append(
                {
                    "type": "threshold",
                    "variable": "current_effective_price",
                    "action": "decrease",
                    "suggested_change": int(max(gap, 0)),
                    "threshold": float(max(price_value - gap, 0)),
                    "message": f"가격이 약 {max(gap, 0):,}원 낮아지거나 잔액이 늘어나면 판단이 개선될 수 있습니다.",
                }
            )

        if days_until_card_due < 7 and expected_card_payment_amount > (
            current_balance * 0.4
        ):
            suggestions.append(
                {
                    "type": "threshold",
                    "variable": "available_budget",
                    "action": "increase",
                    "suggested_change": int(expected_card_payment_amount * 0.2),
                    "threshold": float(
                        current_balance + (expected_card_payment_amount * 0.2)
                    ),
                    "message": "가용예산을 늘리거나 결제 부담 구간이 지난 뒤 재평가하면 판단이 개선될 수 있습니다.",
                }
            )

        if len(suggestions) == 0:
            suggestions.append(
                {
                    "type": "threshold",
                    "variable": "current_effective_price",
                    "action": "wait_for_better_price",
                    "suggested_change": 0,
                    "threshold": price_value,
                    "message": "가격 하락 또는 잔액 증가 시 재평가를 권장합니다.",
                }
            )

        return suggestions[:3]
