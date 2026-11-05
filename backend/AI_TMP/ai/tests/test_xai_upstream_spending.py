"""Spring 이 최근 30일 카드 지출 합계(monthlySpending30d)를 직접 보내는 경우.

거래 목록(recentTransactions)은 최대 50건이라 카드를 많이 쓰는 사용자는 합계가 잘려 하한값이 된다. 그러면
'지금 구매'를 막고 추가 검토로 내릴 수밖에 없었다. 합계를 DB 에서 직접 보내면 잘리지 않으므로 정확히 판정한다.
"""

from __future__ import annotations

import unittest

from .test_budget_integration import WITH_INCOME, evaluate
from .test_decision_severity_and_input_reliability import many_transactions, with_transactions


def spending(value, **flags) -> dict:
    return {
        "monthlySpending30d": {
            "value": value, "source": "spring.card_transactions", "snapshotId": "card-spending-30d:1:20261105", **flags,
        },
        **WITH_INCOME,
    }


class UpstreamSpendingTest(unittest.TestCase):
    def test_합계를_보내면_거래가_50건에서_잘려도_추가_검토로_내리지_않는다(self) -> None:
        rows = many_transactions(50, 8_000)  # 거래 목록은 상한에 걸린 상태

        without_total = evaluate(with_transactions(50_000, rows, WITH_INCOME))
        with_total = evaluate(with_transactions(50_000, rows, spending(400_000)))

        self.assertIn("SPENDING_TRUNCATED", without_total.warnings)
        self.assertEqual(without_total.decision, "REVIEW")
        self.assertNotIn("SPENDING_TRUNCATED", with_total.warnings)
        self.assertNotIn("FINANCE_FIELD_ESTIMATED:monthly_spending_30d", with_total.warnings)
        self.assertEqual(with_total.decision, "BUY_NOW", with_total.warnings)

    def test_합계가_거래_목록보다_크면_합계를_쓴다(self) -> None:
        # 거래 목록은 50건 x 8,000 = 40만 원이지만 실제 30일 지출은 150만 원이다. 소득 300만 원(한도 150만 원) 이면 이미 한도다.
        rows = many_transactions(50, 8_000)

        response = evaluate(with_transactions(50_000, rows, spending(1_500_000)))

        self.assertEqual(response.decision, "NOT_RECOMMENDED", response.warnings)
        self.assertNotIn("SPENDING_TRUNCATED", response.warnings)

    def test_거래가_없어도_합계가_있으면_지출을_안다(self) -> None:
        response = evaluate(with_transactions(50_000, None, spending(400_000)))

        self.assertNotIn("FINANCE_FIELD_DEFAULTED:monthly_spending_30d", response.warnings)
        self.assertFalse(any(w.startswith("SPENDING_UNKNOWN") for w in response.warnings))
        self.assertEqual(response.decision, "BUY_NOW", response.warnings)

    def test_쓸_수_없는_합계는_무시하고_거래_목록으로_계산한다(self) -> None:
        rows = many_transactions(20, 8_000)
        for bad in (0, -5, "abc", None):
            payload = spending(bad if bad is not None else 0)
            if bad is None:
                payload["monthlySpending30d"]["value"] = None
            with self.subTest(value=bad):
                response = evaluate(with_transactions(50_000, rows, payload))
                self.assertNotIn("FINANCE_FIELD_DEFAULTED:monthly_spending_30d", response.warnings)
                self.assertEqual(response.decision, "BUY_NOW", response.warnings)

    def test_기본값이나_추정이라고_밝힌_합계는_믿지_않는다(self) -> None:
        rows = many_transactions(20, 8_000)

        defaulted = evaluate(with_transactions(50_000, rows, spending(400_000, isDefault=True)))
        estimated = evaluate(with_transactions(50_000, rows, spending(400_000, isEstimated=True)))

        # 기본값 표시가 붙은 값은 버리고 거래 목록(20건)에서 다시 계산한다.
        self.assertNotIn("FINANCE_FIELD_DEFAULTED:monthly_spending_30d", defaulted.warnings)
        # 추정이라고 밝힌 값은 쓰되, 추정이므로 '지금 구매'로 올리지 않는다.
        self.assertIn("FINANCE_FIELD_ESTIMATED:monthly_spending_30d", estimated.warnings)
        self.assertNotEqual(estimated.decision, "BUY_NOW")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
