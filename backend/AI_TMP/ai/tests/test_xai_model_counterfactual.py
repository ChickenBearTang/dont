"""반사실 엔진(무엇을 바꾸면 되나) 단위 테스트.

evaluate 를 가짜로 꽂아 엔진의 약속만 고정한다:
  1. 확인된(evaluate 가 통과시킨) 변화만 제안한다.
  2. 사용자가 바꿀 수 있는 값만 건드린다.
  3. 작은 변화부터 시도해 처음 통과한 값을 낸다.
모델과 연결된 왕복 검증은 test_xai_counterfactual_roundtrip.py 에 있다.
"""

from __future__ import annotations

import unittest

from ..xai.model_counterfactual import (
    ACTIONABLE_KEYS,
    DECISION_RANK,
    ModelCounterfactualEngine,
    Outcome,
)

CURRENT = {"current_balance": 900_000.0, "emergency_fund_balance": 150_000.0, "savebox_balance": 150_000.0}
BASE = dict(price=2_500_000.0, monthly_spending=1_300_000.0, current_values=CURRENT)


def _engine(rule, calls=None):
    def evaluate(overrides):
        if calls is not None:
            calls.append(dict(overrides))
        return Outcome(decision=rule(overrides), finance_risk_score=0.1)

    return ModelCounterfactualEngine(evaluate)


class ProposalTest(unittest.TestCase):
    def test_통과한_변화만_제안하고_결과는_확인된_판단이다(self) -> None:
        engine = _engine(lambda o: "REVIEW" if o.get("emergency_fund_balance", 0) >= 600_000 else "NOT_RECOMMENDED")

        results, state = engine.suggest(current_decision="NOT_RECOMMENDED", **BASE)

        self.assertEqual([r["variable"] for r in results], ["emergency_fund_balance"])
        only = results[0]
        self.assertTrue(only["validated"])
        self.assertEqual(only["target_decision"], "REVIEW")
        self.assertGreaterEqual(150_000 + only["suggested_change"], 600_000)
        self.assertEqual(only["threshold"], 150_000 + only["suggested_change"])
        self.assertTrue(state["enabled"])

    def test_가장_작은_통과_변화를_낸다(self) -> None:
        """통과하는 가장 작은 격자 값이어야 한다. 한 칸 작은 값은 통과하지 못해야 한다."""
        passed_at: list[float] = []

        def rule(o):
            if "savebox_balance" in o and o["savebox_balance"] >= 400_000:
                passed_at.append(o["savebox_balance"])
                return "REVIEW"
            return "NOT_RECOMMENDED"

        results, _ = _engine(rule).suggest(current_decision="NOT_RECOMMENDED", **BASE)

        savebox = next(r for r in results if r["variable"] == "savebox_balance")
        self.assertEqual(passed_at[0], savebox["threshold"])
        self.assertLess(savebox["suggested_change"], 400_000 - 150_000 + 70_000)  # 격자 간격 이내

    def test_아무것도_통과하지_못하면_빈_결과와_이유를_준다(self) -> None:
        results, state = _engine(lambda o: "NOT_RECOMMENDED").suggest(
            current_decision="NOT_RECOMMENDED", **BASE
        )

        self.assertEqual(results, [])
        self.assertEqual(state["reason"], "no_single_change_found")

    def test_이미_바로_구매면_제안하지_않고_평가도_하지_않는다(self) -> None:
        calls: list = []

        results, state = _engine(lambda o: "BUY_NOW", calls).suggest(current_decision="BUY_NOW", **BASE)

        self.assertEqual(results, [])
        self.assertEqual(state["reason"], "already_buy_now")
        self.assertEqual(calls, [])

    def test_모르는_판단_이름은_거부한다(self) -> None:
        results, state = _engine(lambda o: "REVIEW").suggest(current_decision="MAYBE", **BASE)

        self.assertEqual(results, [])
        self.assertFalse(state["enabled"])


class TargetTest(unittest.TestCase):
    def test_목표는_지금보다_한_단계_이상_나아진_판단이다(self) -> None:
        """결제일 임박 같은 바꿀 수 없는 요인이 있으면 '바로 구매'는 안 나온다.
        그래도 '추천 안 함'에서 '대기'로 나아지는 변화는 사용자에게 의미 있다."""
        results, _ = _engine(lambda o: "WAIT").suggest(current_decision="NOT_RECOMMENDED", **BASE)

        self.assertTrue(results)
        self.assertTrue(all(r["target_decision"] == "WAIT" for r in results))

    def test_재검토에서는_바로_구매만_개선이다(self) -> None:
        results, _ = _engine(lambda o: "REVIEW").suggest(current_decision="REVIEW", **BASE)
        self.assertEqual(results, [])

        results, _ = _engine(lambda o: "BUY_NOW").suggest(current_decision="REVIEW", **BASE)
        self.assertTrue(results)
        self.assertTrue(all(r["target_decision"] == "BUY_NOW" for r in results))

    def test_대기에서는_재검토_이상이_개선이다(self) -> None:
        results, _ = _engine(lambda o: "REVIEW").suggest(current_decision="WAIT", **BASE)

        self.assertTrue(results)
        self.assertTrue(all(DECISION_RANK[r["target_decision"]] > DECISION_RANK["WAIT"] for r in results))

    def test_같거나_나빠진_판단은_통과로_치지_않는다(self) -> None:
        results, _ = _engine(lambda o: "WAIT").suggest(current_decision="WAIT", **BASE)
        self.assertEqual(results, [])

        results, _ = _engine(lambda o: "NOT_RECOMMENDED").suggest(current_decision="WAIT", **BASE)
        self.assertEqual(results, [])


class ActionableOnlyTest(unittest.TestCase):
    def test_바꿀_수_있는_값만_시도한다(self) -> None:
        calls: list = []
        _engine(lambda o: "NOT_RECOMMENDED", calls).suggest(current_decision="NOT_RECOMMENDED", **BASE)

        self.assertTrue(calls)
        for overrides in calls:
            self.assertEqual(len(overrides), 1)  # 한 번에 하나만 바꾼다
            self.assertTrue(set(overrides) <= ACTIONABLE_KEYS, overrides)
        tried = {key for overrides in calls for key in overrides}
        self.assertEqual(
            tried, {"emergency_fund_balance", "savebox_balance", "current_balance", "product_price"}
        )
        for forbidden in ("days_until_card_due", "monthly_spending_30d", "expected_card_payment_amount"):
            self.assertNotIn(forbidden, tried)

    def test_가격은_내리고_잔액은_올린다(self) -> None:
        calls: list = []
        _engine(lambda o: "NOT_RECOMMENDED", calls).suggest(current_decision="NOT_RECOMMENDED", **BASE)

        for overrides in calls:
            if "product_price" in overrides:
                self.assertLess(overrides["product_price"], BASE["price"])
                self.assertGreater(overrides["product_price"], 0)
            else:
                (key, value), = overrides.items()
                self.assertGreater(value, CURRENT[key])


class FormattingTest(unittest.TestCase):
    def test_금액은_단위에_맞게_반올림된다(self) -> None:
        results, _ = _engine(lambda o: "REVIEW").suggest(current_decision="NOT_RECOMMENDED", **BASE)

        for r in results:
            if r["variable"] == "product_price":
                self.assertEqual(int(r["threshold"]) % 1_000, 0)
            else:
                self.assertEqual(r["suggested_change"] % 10_000, 0)

    def test_문구가_제안과_결과를_그대로_말한다(self) -> None:
        results, _ = _engine(lambda o: "BUY_NOW").suggest(current_decision="REVIEW", **BASE)

        for r in results:
            self.assertIn(f"{r['suggested_change']:,}원", r["message"])
            self.assertIn("바로 구매", r["message"])

    def test_비용이_작은_순서로_최대_3개를_낸다(self) -> None:
        results, _ = _engine(lambda o: "REVIEW").suggest(current_decision="NOT_RECOMMENDED", **BASE)

        self.assertLessEqual(len(results), 3)
        costs = [r["relative_cost"] for r in results]
        self.assertEqual(costs, sorted(costs))

    def test_같은_입력은_같은_결과다(self) -> None:
        rule = lambda o: "REVIEW" if o.get("current_balance", 0) >= 1_500_000 else "NOT_RECOMMENDED"  # noqa: E731

        first = _engine(rule).suggest(current_decision="NOT_RECOMMENDED", **BASE)
        second = _engine(rule).suggest(current_decision="NOT_RECOMMENDED", **BASE)

        self.assertEqual(first, second)


class NonMonotonicTest(unittest.TestCase):
    def test_단조롭지_않은_모델에서도_확인된_값만_낸다(self) -> None:
        """트리 모델은 값을 올렸다고 항상 좋아지지 않는다. 통과 구간 밖의 값은 내지 않는다."""
        band = lambda o: "REVIEW" if 500_000 <= o.get("emergency_fund_balance", 0) <= 700_000 else "NOT_RECOMMENDED"  # noqa: E731
        evaluated: dict[float, str] = {}

        def evaluate(o):
            decision = band(o)
            if "emergency_fund_balance" in o:
                evaluated[o["emergency_fund_balance"]] = decision
            return Outcome(decision)

        results, _ = ModelCounterfactualEngine(evaluate).suggest(current_decision="NOT_RECOMMENDED", **BASE)

        emergency = next(r for r in results if r["variable"] == "emergency_fund_balance")
        self.assertEqual(evaluated[emergency["threshold"]], "REVIEW")
        self.assertTrue(500_000 <= emergency["threshold"] <= 700_000)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class AnalyzerScenarioTest(unittest.TestCase):
    """analyzer.decide_scenario: 바꾼 조건이 실제 판단 계산에 반영되는가."""

    def _analyzer(self, signals):
        from ..xai.analyzer import ExplainabilityAnalyzer
        from ..xai.counterfactuals import CounterfactualEngine

        return ExplainabilityAnalyzer(
            finance_profile={
                "current_balance": 900_000, "emergency_fund_balance": 150_000,
                "savebox_balance": 150_000, "expected_card_payment_amount": 700_000,
                "days_until_card_due": 2, "monthly_spending_30d": 1_300_000,
            },
            dice_counterfactual_engine=CounterfactualEngine(),
            scenario_signals=signals,
        )

    def test_재무_모델_신호가_없으면_바꾼_프로필로_휴리스틱_판단을_다시_계산한다(self) -> None:
        """모델이 없을 때 판단은 프로필 값에서 직접 나온다. 바꾼 값이 반영되지 않으면
        어떤 제안도 효과가 없는 것으로 보이거나 엉뚱하게 통과한다."""
        analyzer = self._analyzer(lambda price, profile: ({}, {}))

        base = analyzer.decide_scenario(price_value=2_500_000, overrides={}, window_stats=None)
        raised = analyzer.decide_scenario(
            price_value=2_500_000,
            overrides={"emergency_fund_balance": 5_000_000.0, "savebox_balance": 5_000_000.0},
            window_stats=None,
        )

        self.assertEqual(base.decision, "NOT_RECOMMENDED")
        self.assertGreater(DECISION_RANK[raised.decision], DECISION_RANK[base.decision])

    def test_바꾼_프로필과_가격이_모델_호출에_그대로_전달된다(self) -> None:
        seen = []

        def signals(price, profile):
            seen.append((price, dict(profile)))
            return {}, {}

        analyzer = self._analyzer(signals)
        analyzer.decide_scenario(
            price_value=2_500_000,
            overrides={"product_price": 900_000.0, "current_balance": 1_800_000.0},
            window_stats=None,
        )

        price, profile = seen[0]
        self.assertEqual(price, 900_000)
        self.assertEqual(profile["current_balance"], 1_800_000.0)
        self.assertEqual(profile["emergency_fund_balance"], 150_000)  # 바꾸지 않은 값은 그대로

    def test_원래_분석기의_상태는_바뀌지_않는다(self) -> None:
        analyzer = self._analyzer(lambda price, profile: ({}, {}))
        before = dict(analyzer._finance_profile)

        analyzer.decide_scenario(
            price_value=2_500_000, overrides={"emergency_fund_balance": 9_000_000.0}, window_stats=None
        )

        self.assertEqual(analyzer._finance_profile, before)

    def test_scenario_signals가_없으면_거부한다(self) -> None:
        analyzer = self._analyzer(None)

        with self.assertRaises(RuntimeError):
            analyzer.decide_scenario(price_value=1000, overrides={}, window_stats=None)


class MissingFinanceSignalTest(unittest.TestCase):
    """재무 모델 신호가 없을 때 위험도 0(안전)으로 판단하면 안 된다.

    규칙 엔진은 finance_model_* 점수가 '있는지'로 분기한다. 예전에는 분석기가 신호가
    없어도 이 키를 0.0 으로 채워서, 모델이 죽으면 항상 '위험 없음'으로 판단했다.
    """

    def test_신호가_없으면_모델_점수를_점수표에_넣지_않는다(self) -> None:
        from ..xai.analyzer import ExplainabilityAnalyzer
        from ..xai.counterfactuals import CounterfactualEngine

        analyzer = ExplainabilityAnalyzer(
            finance_profile={"current_balance": 900_000, "emergency_fund_balance": 150_000,
                             "savebox_balance": 150_000, "expected_card_payment_amount": 700_000,
                             "days_until_card_due": 2, "monthly_spending_30d": 1_300_000},
            dice_counterfactual_engine=CounterfactualEngine(),
        )

        scores = analyzer._build_feature_scores({"price_int": 2_500_000, "missing_fields": []}, window_stats=None)

        self.assertNotIn("finance_model_risk_score", scores)
        self.assertNotIn("finance_model_affordability_score", scores)

    def test_신호가_있으면_점수표에_들어간다(self) -> None:
        from ..xai.analyzer import ExplainabilityAnalyzer
        from ..xai.counterfactuals import CounterfactualEngine

        analyzer = ExplainabilityAnalyzer(
            finance_profile={"current_balance": 900_000, "emergency_fund_balance": 150_000,
                             "savebox_balance": 150_000, "expected_card_payment_amount": 700_000,
                             "days_until_card_due": 2, "monthly_spending_30d": 1_300_000},
            dice_counterfactual_engine=CounterfactualEngine(),
            finance_model_signal={"finance_model_risk_score": 0.8, "finance_model_affordability_score": -0.8},
        )

        scores = analyzer._build_feature_scores({"price_int": 2_500_000, "missing_fields": []}, window_stats=None)

        self.assertEqual(scores["finance_model_risk_score"], 0.8)
        self.assertEqual(scores["finance_model_affordability_score"], -0.8)

    def test_모델이_없을_때_빠듯한_사용자를_안전하다고_판단하지_않는다(self) -> None:
        from ..xai.analyzer import ExplainabilityAnalyzer
        from ..xai.counterfactuals import CounterfactualEngine

        analyzer = ExplainabilityAnalyzer(
            finance_profile={"current_balance": 900_000, "emergency_fund_balance": 150_000,
                             "savebox_balance": 150_000, "expected_card_payment_amount": 700_000,
                             "days_until_card_due": 2, "monthly_spending_30d": 1_300_000},
            dice_counterfactual_engine=CounterfactualEngine(),
        )
        scores = analyzer._build_feature_scores({"price_int": 2_500_000, "missing_fields": []}, window_stats=None)

        outcome = analyzer._decision_engine.decide(scores)

        self.assertEqual(outcome.final_decision, "NOT_RECOMMENDED")
        self.assertEqual(outcome.fired_rule_ids, ["FIN_HIGH_STRESS"])
