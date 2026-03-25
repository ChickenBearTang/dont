from __future__ import annotations

import unittest

from ..xai.decision_engine import DecisionEngine


class DecisionEngineBranchCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_not_recommended_branch(self) -> None:
        result = self.engine.decide(
            {
                "current_price": 0.5,
                "avg_price_30d": 0.5,
                "product_price_vs_monthly_spending": 2.5,
                "emergency_fund_balance": 0.75,
                "projected_balance_after_purchase": -0.625,
                "days_until_card_due": 0.5,
            }
        )

        self.assertEqual(result.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(result.fired_rule_ids, ["FIN_HIGH_STRESS"])

    def test_buy_now_branch(self) -> None:
        result = self.engine.decide(
            {
                "current_price": 0.91,
                "avg_price_30d": 0.5,
                "product_price_vs_monthly_spending": 0.0125,
                "emergency_fund_balance": 0.75,
                "projected_balance_after_purchase": 1.86,
                "days_until_card_due": 0.5,
            }
        )

        self.assertEqual(result.final_decision, "BUY_NOW")
        self.assertEqual(result.fired_rule_ids, ["PRICE_FAVORABLE_AND_AFFORDABLE"])

    def test_wait_branch(self) -> None:
        result = self.engine.decide(
            {
                "current_price": 0.5,
                "avg_price_30d": 0.5,
                "product_price_vs_monthly_spending": 0.5,
                "emergency_fund_balance": 0.75,
                "projected_balance_after_purchase": 1.0,
                "days_until_card_due": 0.16,
            }
        )

        self.assertEqual(result.final_decision, "WAIT")
        self.assertEqual(result.fired_rule_ids, ["TIME_NEAR_CARD_DUE_DATE"])

    def test_review_branch(self) -> None:
        result = self.engine.decide(
            {
                "current_price": 0.5,
                "avg_price_30d": 0.3,
                "product_price_vs_monthly_spending": 1.0,
                "emergency_fund_balance": 0.5,
                "projected_balance_after_purchase": 0.5,
                "days_until_card_due": 0.5,
            }
        )

        self.assertEqual(result.final_decision, "REVIEW")
        self.assertEqual(result.fired_rule_ids, ["DECISION_REVIEW_REQUIRED"])


if __name__ == "__main__":
    unittest.main()
