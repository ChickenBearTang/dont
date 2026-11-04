"""5·3·2 예산 규칙 테스트.

정의 (사용자 결정 + 제가 둔 가정)
  - 소득을 생활비 5 / 투자 3 / 저축 2 로 나눈다. 물건 가격은 생활비 5 구역에서 나가는 돈이다.
  - 5 구역 한도 = 월 소득 x 0.5
  - 5 구역 사용량 = 고정지출(+매달 적립하는 비상금) + 최근 30일 변동 지출(거래에서 계산)
  - 이번 구매 후 사용률 = (사용량 + 가격) / 한도
가정: 카드 거래(변동 지출)와 고정지출은 겹치지 않는다. 고정지출에는 매달 비상금 적립액이
포함돼 있다. 둘 다 앞단(Spring)이 그렇게 보낸다는 전제이며 어긋나면 사용률이 틀린다.
"""

from __future__ import annotations

import unittest

from ..xai.budget_rule import (
    EMERGENCY_COVER_TARGET_MONTHS,
    TIGHT_RATIO,
    ALREADY_OVER_EXPLANATION_FLOOR,
    OVER_EXPLANATION_FLOOR,
    TIGHT_EXPLANATION_SCORE,
    explanation_score,
    ZONE_INVEST_SHARE,
    ZONE_NEEDS_SHARE,
    ZONE_SAVINGS_SHARE,
    BudgetStatus,
    assess_budget,
    score_from_ratio,
    status_from_ratios,
)

BASE = dict(monthly_income=3_000_000.0, fixed_expense=900_000.0, variable_spending_30d=400_000.0, price=100_000.0)
# 한도 150만, 사용 130만 -> 이번 구매 후 140만 (93%)


class ZoneConstantsTest(unittest.TestCase):
    def test_5_3_2는_합이_1이다(self) -> None:
        self.assertEqual((ZONE_NEEDS_SHARE, ZONE_INVEST_SHARE, ZONE_SAVINGS_SHARE), (0.5, 0.3, 0.2))
        self.assertAlmostEqual(ZONE_NEEDS_SHARE + ZONE_INVEST_SHARE + ZONE_SAVINGS_SHARE, 1.0)


class AssessTest(unittest.TestCase):
    def test_한도_사용량_사용률을_계산한다(self) -> None:
        a = assess_budget(**BASE)

        self.assertEqual(a.limit, 1_500_000.0)
        self.assertEqual(a.used_before, 1_300_000.0)
        self.assertEqual(a.used_after, 1_400_000.0)
        self.assertAlmostEqual(a.ratio_before, 1_300_000 / 1_500_000)
        self.assertAlmostEqual(a.ratio_after, 1_400_000 / 1_500_000)
        self.assertEqual(a.headroom_before, 200_000.0)
        self.assertEqual(a.headroom_after, 100_000.0)
        self.assertEqual(a.overshoot, 0.0)

    def test_여유가_넉넉하면_WITHIN(self) -> None:
        a = assess_budget(**{**BASE, "price": 10_000.0})

        self.assertEqual(a.status, BudgetStatus.WITHIN)
        self.assertGreater(a.score, 0)

    def test_한도_근처면_TIGHT(self) -> None:
        a = assess_budget(**BASE)  # 93%

        self.assertEqual(a.status, BudgetStatus.TIGHT)

    def test_이번_구매로_한도를_넘으면_OVER이고_초과액을_알려준다(self) -> None:
        a = assess_budget(**{**BASE, "price": 300_000.0})  # 160만 / 150만

        self.assertEqual(a.status, BudgetStatus.OVER)
        self.assertEqual(a.overshoot, 100_000.0)
        self.assertLess(a.score, 0)

    def test_이미_한도를_넘었으면_ALREADY_OVER(self) -> None:
        a = assess_budget(**{**BASE, "variable_spending_30d": 800_000.0, "price": 10_000.0})  # 170만 > 150만

        self.assertEqual(a.status, BudgetStatus.ALREADY_OVER)
        self.assertGreater(a.ratio_before, 1.0)

    def test_가격이_0이면_구매_전후가_같다(self) -> None:
        a = assess_budget(**{**BASE, "price": 0.0})

        self.assertEqual(a.ratio_before, a.ratio_after)

    def test_정확히_한도와_같으면_넘지_않은_것이다(self) -> None:
        a = assess_budget(**{**BASE, "price": 200_000.0})  # 150만 / 150만

        self.assertEqual(a.status, BudgetStatus.TIGHT)
        self.assertEqual(a.overshoot, 0.0)


class UnavailableTest(unittest.TestCase):
    def test_소득이_없거나_0이하면_판단하지_않는다(self) -> None:
        for income in (None, 0.0, -100.0):
            with self.subTest(income=income):
                a = assess_budget(**{**BASE, "monthly_income": income})
                self.assertEqual(a.status, BudgetStatus.UNAVAILABLE)
                self.assertEqual(a.reason, "income_unknown_or_not_positive")
                self.assertIsNone(a.ratio_after)

    def test_고정지출이나_변동지출을_모르면_판단하지_않는다(self) -> None:
        self.assertEqual(assess_budget(**{**BASE, "fixed_expense": None}).reason, "fixed_expense_unknown")
        self.assertEqual(assess_budget(**{**BASE, "variable_spending_30d": None}).reason, "spending_unknown")

    def test_가격이_없거나_음수면_판단하지_않는다(self) -> None:
        for price in (None, -1.0):
            with self.subTest(price=price):
                self.assertEqual(assess_budget(**{**BASE, "price": price}).reason, "price_invalid")

    def test_숫자가_아니거나_비유한이면_판단하지_않는다(self) -> None:
        for bad in ("많음", float("nan"), float("inf")):
            with self.subTest(bad=bad):
                self.assertEqual(assess_budget(**{**BASE, "monthly_income": bad}).status, BudgetStatus.UNAVAILABLE)

    def test_음수_고정지출은_0으로_본다(self) -> None:
        self.assertEqual(assess_budget(**{**BASE, "fixed_expense": -5.0}).fixed_expense, 0.0)

    def test_기본값으로_채웠을지_모르는_값은_이_함수가_추측하지_않는다(self) -> None:
        """호출하는 쪽(analyzer)이 출처가 DEFAULT 인 값을 None 으로 바꿔 넘긴다. 여기서는 None 이면 판단 불가다."""
        a = assess_budget(monthly_income=None, fixed_expense=None, variable_spending_30d=None, price=1.0)

        self.assertEqual(a.status, BudgetStatus.UNAVAILABLE)


class StatusAndScoreTest(unittest.TestCase):
    def test_경계값(self) -> None:
        self.assertEqual(status_from_ratios(0.5, TIGHT_RATIO), BudgetStatus.WITHIN)
        self.assertEqual(status_from_ratios(0.5, TIGHT_RATIO + 1e-9), BudgetStatus.TIGHT)
        self.assertEqual(status_from_ratios(0.5, 1.0), BudgetStatus.TIGHT)
        self.assertEqual(status_from_ratios(0.5, 1.0 + 1e-9), BudgetStatus.OVER)
        self.assertEqual(status_from_ratios(1.0 + 1e-9, 1.2), BudgetStatus.ALREADY_OVER)

    def test_점수는_사용률이_클수록_작고_범위_안이다(self) -> None:
        ratios = [0.0, 0.3, 0.7, 0.9, 1.0, 1.15, 1.3, 2.0, 10.0]
        scores = [score_from_ratio(r) for r in ratios]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(-1.0 <= s <= 1.0 for s in scores))
        self.assertEqual(score_from_ratio(1.0), 0.0)
        self.assertEqual(score_from_ratio(0.7), 1.0)
        self.assertEqual(score_from_ratio(1.3), -1.0)


class EmergencyCoverTest(unittest.TestCase):
    def test_비상금이_몇_달치_지출을_덮는지_알려준다(self) -> None:
        a = assess_budget(**BASE, emergency_fund_balance=2_600_000.0)  # (90+40)만 = 130만 -> 2개월

        self.assertAlmostEqual(a.emergency_cover_months, 2.0)

    def test_비상금을_모르면_None(self) -> None:
        self.assertIsNone(assess_budget(**BASE).emergency_cover_months)

    def test_목표_개월수는_3이다(self) -> None:
        self.assertEqual(EMERGENCY_COVER_TARGET_MONTHS, 3.0)


class SerializationTest(unittest.TestCase):
    def test_사전_형태로_바꿀_수_있다(self) -> None:
        d = assess_budget(**BASE).to_dict()

        self.assertEqual(d["status"], "tight")
        self.assertEqual(d["limit"], 1_500_000.0)
        self.assertIn("ratio_after", d)

    def test_판단_불가도_사유와_함께_직렬화된다(self) -> None:
        d = assess_budget(**{**BASE, "monthly_income": None}).to_dict()

        self.assertEqual(d["status"], "unavailable")
        self.assertEqual(d["reason"], "income_unknown_or_not_positive")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


def _assess(price: float):
    # 한도 150만 원, 사용 130만 원
    return assess_budget(monthly_income=3_000_000, fixed_expense=900_000, variable_spending_30d=400_000, price=price)


class ExplanationScoreTest(unittest.TestCase):
    """설명용 점수의 부호는 규칙 판단(상태)과 같은 방향이어야 한다."""

    def test_여유_있으면_양수(self) -> None:
        a = _assess(10_000)
        self.assertEqual(a.status, BudgetStatus.WITHIN)
        self.assertGreater(explanation_score(a), 0.3)

    def test_빠듯함은_사용률_점수가_양수여도_설명은_음수(self) -> None:
        a = _assess(100_000)  # (130+10)/150 = 0.933 -> TIGHT
        self.assertEqual(a.status, BudgetStatus.TIGHT)
        self.assertGreater(a.score, 0)  # 규칙 점수만 보면 '유리'로 보이는 구간
        self.assertEqual(explanation_score(a), TIGHT_EXPLANATION_SCORE)
        self.assertLess(explanation_score(a), 0)

    def test_한도를_조금만_넘어도_눈에_띄는_크기의_음수(self) -> None:
        a = _assess(210_000)  # (130+21)/150 = 1.0067 -> OVER, 사용률 점수는 -0.02 로 미미
        self.assertEqual(a.status, BudgetStatus.OVER)
        self.assertGreater(a.score, OVER_EXPLANATION_FLOOR)
        self.assertEqual(explanation_score(a), OVER_EXPLANATION_FLOOR)

    def test_이미_넘은_상태는_더_강한_음수(self) -> None:
        a = assess_budget(monthly_income=3_000_000, fixed_expense=1_500_000, variable_spending_30d=100_000, price=1_000)
        self.assertEqual(a.status, BudgetStatus.ALREADY_OVER)
        self.assertEqual(explanation_score(a), ALREADY_OVER_EXPLANATION_FLOOR)

    def test_크게_넘으면_사용률_점수를_그대로_쓴다(self) -> None:
        a = _assess(600_000)
        self.assertEqual(explanation_score(a), a.score)
        self.assertLess(a.score, OVER_EXPLANATION_FLOOR)

    def test_판단_불가면_None(self) -> None:
        self.assertIsNone(explanation_score(assess_budget(monthly_income=None, fixed_expense=0, variable_spending_30d=0, price=1)))


class DecisionEngineBudgetTest(unittest.TestCase):
    """규칙 엔진이 예산 사용률을 판단에 반영한다. 키가 없으면(앞단이 소득을 안 보내면) 이전과 같다."""

    @staticmethod
    def _decide(**scores):
        from ..xai.decision_engine import DecisionEngine

        base = {"current_price": 0.2, "avg_price_30d": 0.0, "price_model_gap_score": 0.0,
                "finance_model_risk_score": -0.6, "finance_model_affordability_score": 0.6,
                "days_until_card_due": 0.7}
        return DecisionEngine().decide({**base, **scores})

    def test_이미_한도를_넘었으면_구매_비추천(self) -> None:
        out = self._decide(budget_ratio_before=1.2, budget_ratio_after=1.25)

        self.assertEqual(out.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(out.fired_rule_ids, ["BUDGET_ZONE_ALREADY_EXCEEDED"])

    def test_이번_구매로_한도를_넘으면_구매_비추천(self) -> None:
        out = self._decide(budget_ratio_before=0.8, budget_ratio_after=1.1)

        self.assertEqual(out.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(out.fired_rule_ids, ["BUDGET_ZONE_EXCEEDED"])

    def test_초과폭이_클수록_확신도가_높다(self) -> None:
        small = self._decide(budget_ratio_before=0.8, budget_ratio_after=1.05).decision_confidence
        large = self._decide(budget_ratio_before=0.8, budget_ratio_after=1.6).decision_confidence

        self.assertGreater(large, small)

    def test_빠듯하면_가격이_좋아도_관망이다(self) -> None:
        out = self._decide(budget_ratio_before=0.8, budget_ratio_after=0.95, current_price=1.0, avg_price_30d=1.0)

        self.assertEqual(out.final_decision, "WAIT")
        self.assertEqual(out.fired_rule_ids, ["BUDGET_ZONE_NEARLY_FULL"])

    def test_한도_안에서_여유가_있고_재무도_안전하면_바로_구매(self) -> None:
        out = self._decide(budget_ratio_before=0.4, budget_ratio_after=0.5)

        self.assertEqual(out.final_decision, "BUY_NOW")
        self.assertEqual(out.fired_rule_ids, ["BUDGET_WITHIN_AND_AFFORDABLE"])

    def test_한도_안이어도_재무_모델이_주의를_주면_바로_구매가_아니다(self) -> None:
        out = self._decide(budget_ratio_before=0.4, budget_ratio_after=0.5, finance_model_risk_score=0.4,
                           finance_model_affordability_score=-0.4)

        self.assertEqual(out.final_decision, "WAIT")

    def test_한도_안이어도_결제일이_임박하면_바로_구매가_아니다(self) -> None:
        out = self._decide(budget_ratio_before=0.4, budget_ratio_after=0.5, days_until_card_due=0.05)

        self.assertNotEqual(out.final_decision, "BUY_NOW")

    def test_예산이_초과면_재무_모델이_안전해도_구매_비추천(self) -> None:
        out = self._decide(budget_ratio_before=0.9, budget_ratio_after=1.3, finance_model_risk_score=-0.9)

        self.assertEqual(out.final_decision, "NOT_RECOMMENDED")

    def test_예산_키가_없으면_예전_판단과_같다(self) -> None:
        with_budget_absent = self._decide()

        self.assertNotIn("BUDGET", " ".join(with_budget_absent.fired_rule_ids))

    def test_재무_모델_신호가_없는_휴리스틱_분기에서도_초과는_막는다(self) -> None:
        from ..xai.decision_engine import DecisionEngine

        out = DecisionEngine().decide({
            "current_price": 0.1, "product_price_vs_monthly_spending": 0.1, "emergency_fund_balance": 3.0,
            "projected_balance_after_purchase": 3.0, "days_until_card_due": 0.9,
            "budget_ratio_before": 0.8, "budget_ratio_after": 1.2,
        })

        self.assertEqual(out.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(out.fired_rule_ids, ["BUDGET_ZONE_EXCEEDED"])

    def test_휴리스틱_분기에서는_예산이_여유여도_바로_구매로_올리지_않는다(self) -> None:
        from ..xai.decision_engine import DecisionEngine

        out = DecisionEngine().decide({
            "current_price": 0.1, "product_price_vs_monthly_spending": 0.1, "emergency_fund_balance": 3.0,
            "projected_balance_after_purchase": 3.0, "days_until_card_due": 0.9,
            "budget_ratio_before": 0.3, "budget_ratio_after": 0.35,
        })

        self.assertNotEqual(out.final_decision, "BUY_NOW")
