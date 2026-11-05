"""E2E 점검에서 드러난 판정 로직 문제 두 가지를 고정한다.

  1) 심각도 뒤집힘: 예산이 '빠듯함'(→ 관망)이면 재무 모델의 고위험(→ 비추천) 판정을 덮어썼다.
     그래서 같은 사람이 가격이 오르면 비추천 → 관망 → 비추천으로 움직였다 (중간 구간에서 판단이 좋아짐).
  2) 믿을 수 없는 입력에서 '지금 구매': 월 지출이 하한값(거래가 50건에서 잘림)이거나 재무 입력이 기본값인데도
     BUY_NOW 가 나왔다. 실제로는 한도를 넘는 사용자가 '여유'로 읽혔다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest  # noqa: E402

from ..xai.decision_engine import DecisionEngine  # noqa: E402
from .test_budget_integration import WITH_INCOME, evaluate, request  # noqa: E402

SEVERITY = {"BUY_NOW": 0, "REVIEW": 1, "WAIT": 2, "NOT_RECOMMENDED": 3}


def scores(**override):
    base = {
        "current_price": 0.5, "avg_price_30d": 0.0, "price_model_gap_score": 0.0,
        "product_price_vs_monthly_spending": 0.3, "emergency_fund_balance": 3.0,
        "projected_balance_after_purchase": 3.0, "days_until_card_due": 0.6,
    }
    base.update(override)
    return base


class SeverityOrderTest(unittest.TestCase):
    engine = DecisionEngine()

    def test_빠듯해도_재무_모델이_고위험이면_비추천이다(self) -> None:
        outcome = self.engine.decide(scores(
            budget_ratio_before=0.8, budget_ratio_after=0.95,
            finance_model_risk_score=0.7, finance_model_affordability_score=-0.7,
        ))

        self.assertEqual(outcome.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(outcome.fired_rule_ids, ["FINANCE_MODEL_HIGH_RISK"])

    def test_빠듯하고_재무_모델이_안전하면_관망이다(self) -> None:
        outcome = self.engine.decide(scores(
            budget_ratio_before=0.8, budget_ratio_after=0.95,
            finance_model_risk_score=-0.5, finance_model_affordability_score=0.5,
        ))

        self.assertEqual(outcome.final_decision, "WAIT")
        self.assertEqual(outcome.fired_rule_ids, ["BUDGET_ZONE_NEARLY_FULL"])

    def test_재무_모델이_없는_경로도_고스트레스면_빠듯함보다_비추천이_먼저다(self) -> None:
        outcome = self.engine.decide(scores(
            budget_ratio_before=0.8, budget_ratio_after=0.95,
            product_price_vs_monthly_spending=4.0, emergency_fund_balance=0.1, projected_balance_after_purchase=-1.0,
        ))

        self.assertEqual(outcome.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(outcome.fired_rule_ids, ["FIN_HIGH_STRESS"])

    def test_한도_초과는_그대로_비추천이다(self) -> None:
        for before, after, rule in ((0.8, 1.2, "BUDGET_ZONE_EXCEEDED"), (1.1, 1.3, "BUDGET_ZONE_ALREADY_EXCEEDED")):
            outcome = self.engine.decide(scores(
                budget_ratio_before=before, budget_ratio_after=after,
                finance_model_risk_score=-0.9, finance_model_affordability_score=0.9,
            ))
            self.assertEqual(outcome.final_decision, "NOT_RECOMMENDED")
            self.assertEqual(outcome.fired_rule_ids, [rule])


class InputReliabilityCapTest(unittest.TestCase):
    engine = DecisionEngine()
    safe_within = staticmethod(lambda: scores(
        budget_ratio_before=0.5, budget_ratio_after=0.6,
        finance_model_risk_score=-0.6, finance_model_affordability_score=0.6,
    ))

    def test_믿을_수_있는_입력이면_여유_있는_구매는_바로_구매다(self) -> None:
        outcome = self.engine.decide(self.safe_within(), inputs_reliable=True)

        self.assertEqual(outcome.final_decision, "BUY_NOW")

    def test_믿을_수_없는_입력이면_바로_구매를_막고_추가_검토로_내린다(self) -> None:
        outcome = self.engine.decide(self.safe_within(), inputs_reliable=False)

        self.assertEqual(outcome.final_decision, "REVIEW")
        self.assertIn(DecisionEngine.BLOCKED_BUY_RULE_ID, outcome.fired_rule_ids)
        self.assertLessEqual(outcome.decision_confidence, 0.5)

    def test_가격이_유리해서_나오는_바로_구매도_막는다(self) -> None:
        favorable = scores(
            current_price=0.9, avg_price_30d=0.8,
            finance_model_risk_score=-0.6, finance_model_affordability_score=0.6,
        )
        self.assertEqual(self.engine.decide(favorable).final_decision, "BUY_NOW")

        self.assertEqual(self.engine.decide(favorable, inputs_reliable=False).final_decision, "REVIEW")

    def test_구매를_말리는_판단은_입력이_부실해도_그대로다(self) -> None:
        over = scores(
            budget_ratio_before=0.8, budget_ratio_after=1.2,
            finance_model_risk_score=-0.6, finance_model_affordability_score=0.6,
        )
        tight = {**over, "budget_ratio_after": 0.95}

        self.assertEqual(self.engine.decide(over, inputs_reliable=False).final_decision, "NOT_RECOMMENDED")
        self.assertEqual(self.engine.decide(tight, inputs_reliable=False).final_decision, "WAIT")


def many_transactions(count: int, amount: int = 8_000) -> list[dict]:
    """최근 30일 안에 count 건. Spring 은 최대 50건만 보내므로 50건이면 잘렸을 수 있다."""
    today = datetime.now(timezone.utc)
    return [
        {
            "transactionDate": (today - timedelta(days=i % 25)).strftime("%Y%m%d"), "transactionTime": "120000",
            "merchantName": "m", "categoryName": "c", "transactionAmount": amount,
        }
        for i in range(count)
    ]


def with_transactions(price: int, rows: list[dict] | None, extra: dict | None = None) -> PurchaseXaiEvaluationRequest:
    payload = request(price, extra).model_dump(by_alias=True)
    payload["recentTransactions"] = rows if rows is not None else []
    return PurchaseXaiEvaluationRequest.model_validate(payload)


class ServiceReliabilityTest(unittest.TestCase):
    def test_정상_입력이면_여유_있는_구매는_바로_구매다(self) -> None:
        response = evaluate(with_transactions(50_000, many_transactions(20), WITH_INCOME))

        self.assertEqual(response.decision, "BUY_NOW", response.warnings)
        self.assertNotIn("INPUT_UNRELIABLE", [f.code for f in response.top_factors])

    def test_거래가_50건에서_잘렸으면_바로_구매가_아니라_추가_검토다(self) -> None:
        response = evaluate(with_transactions(50_000, many_transactions(50), WITH_INCOME))

        self.assertIn("SPENDING_TRUNCATED", response.warnings)
        self.assertEqual(response.decision, "REVIEW")
        first = response.top_factors[0]
        self.assertEqual(first.code, "INPUT_UNRELIABLE")
        self.assertIn("일부만 집계", first.label)
        self.assertIn("일부만 집계", response.summary)

    def test_월_지출이_기본값이면_바로_구매가_아니라_추가_검토다(self) -> None:
        response = evaluate(with_transactions(50_000, None, WITH_INCOME))

        self.assertTrue(any(w.startswith("FINANCE_FIELD_DEFAULTED:monthly_spending_30d") for w in response.warnings))
        self.assertNotEqual(response.decision, "BUY_NOW")

    def test_소득과_고정지출을_추정한_값은_막지_않는다(self) -> None:
        estimated = {
            "availableFixedIncome": {"value": 3_000_000, "source": "s", "snapshotId": "s", "isEstimated": True},
            "availableFixedExpense": {"value": 900_000, "source": "s", "snapshotId": "s", "isEstimated": True},
        }
        response = evaluate(with_transactions(50_000, many_transactions(20), estimated))

        self.assertEqual(response.decision, "BUY_NOW", response.warnings)
        self.assertIn("FINANCE_FIELD_ESTIMATED:available_fixed_income", response.warnings)

    def test_믿을_수_없는_입력에서는_바로_구매를_목표로_한_제안이_나오지_않는다(self) -> None:
        response = evaluate(with_transactions(130_000, many_transactions(50), WITH_INCOME))

        self.assertNotIn("BUY_NOW", [c.target_decision for c in response.counterfactuals])


class PriceMonotonicityTest(unittest.TestCase):
    """같은 사람의 가격만 올렸을 때 판단이 나아지면 안 된다 (BUY_NOW < REVIEW < WAIT < NOT_RECOMMENDED)."""

    PRICES = (50_000, 100_000, 130_000, 170_000, 200_000, 220_000, 260_000, 300_000, 450_000, 700_000)

    def _sweep(self, finance: dict, income: dict, *, count: int, amount: int) -> list[str]:
        return [
            evaluate(with_transactions(price, many_transactions(count, amount), {**finance, **income})).decision
            for price in self.PRICES
        ]

    def _assert_monotonic(self, decisions: list[str]) -> None:
        severity = [SEVERITY[d] for d in decisions]
        self.assertEqual(severity, sorted(severity), f"가격이 오르는데 판단이 나아졌다: {list(zip(self.PRICES, decisions))}")

    def test_비상금이_없는_사용자도_가격이_오를수록_나빠지기만_한다(self) -> None:
        # E2E 에서 d10 이 13~17만 원 비추천 → 20~30만 원 관망 → 45만 원 비추천이던 사람과 같은 모양:
        # 월 지출 40만, 고정지출 60만, 소득 260만 (한도 130만), 비상금 0.
        pv = lambda v: {"value": v, "source": "t", "snapshotId": "s", "isDefault": False, "isEstimated": False}  # noqa: E731
        finance = {
            "currentBalance": pv(1_300_000), "emergencyFundBalance": pv(0), "saveboxBalance": pv(0),
            "expectedCardPaymentAmount": pv(116_600), "daysUntilCardDue": pv(9),
        }
        income = {
            "availableFixedIncome": {"value": 2_600_000, "source": "s", "snapshotId": "s"},
            "availableFixedExpense": {"value": 600_000, "source": "s", "snapshotId": "s"},
        }

        decisions = self._sweep(finance, income, count=20, amount=20_000)

        self._assert_monotonic(decisions)
        # 이 사용자는 재무 모델이 고위험이라 13만 원부터 비추천이고, 빠듯함 구간(20~30만 원)에서도 비추천이어야 한다.
        by_price = dict(zip(self.PRICES, decisions))
        self.assertEqual(by_price[220_000], "NOT_RECOMMENDED")

    def test_여유_있는_사용자도_가격이_오를수록_나빠지기만_한다(self) -> None:
        self._assert_monotonic(self._sweep({}, WITH_INCOME, count=20, amount=8_000))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
