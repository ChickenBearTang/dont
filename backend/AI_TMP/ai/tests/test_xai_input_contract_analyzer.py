"""analyzer 가 입력 계약을 쓰는지, 기본값 표가 한 곳에만 있는지 검증한다."""

from __future__ import annotations

import re
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ..models import CrawlResult, HotDeal
from ..xai.analyzer import ExplainabilityAnalyzer
from ..xai.counterfactuals import CounterfactualEngine
from ..xai.input_contract import (
    InputContractViolation,
    Origin,
    RawField,
    resolve_finance_profile,
)

ANALYZER_SOURCE = Path(__file__).resolve().parents[1] / "xai" / "analyzer.py"


def _analyzer(**kwargs: object) -> ExplainabilityAnalyzer:
    """DiCE 같은 무거운 엔진 없이 규칙 기반 엔진만 쓴다."""
    fallback = CounterfactualEngine()
    return ExplainabilityAnalyzer(
        counterfactual_engine=fallback,
        dice_counterfactual_engine=fallback,
        **kwargs,  # type: ignore[arg-type]
    )


def _crawl() -> CrawlResult:
    return CrawlResult(
        source="fixture",
        fetched_at=datetime(2026, 8, 21, tzinfo=timezone.utc),
        items=[HotDeal(title="노트북", url="https://fixture.invalid/1", price="1,200,000")],
    )


class AnalyzerUsesContractTest(unittest.TestCase):
    def test_프로필_없이_만들면_예전_기본값과_같고_전부_default로_기록된다(self) -> None:
        """호환 모드: 숫자는 예전과 똑같고, 달라진 것은 '기본값이라는 사실'이 남는 것뿐."""
        payload = _analyzer().analyze_crawl_result(_crawl())

        self.assertEqual(
            payload["finance_profile"],
            {
                "current_balance": 1_500_000.0,
                "emergency_fund_balance": 600_000.0,
                "savebox_balance": 600_000.0,
                "expected_card_payment_amount": 200_000.0,
                "days_until_card_due": 14,
            },
        )
        report = payload["input_contract"]
        self.assertEqual(report["default_fallback_rate"], 1.0)
        self.assertIn("current_balance", report["defaulted_fields"])

    def test_완전한_프로필을_주면_default_fallback_rate는_0이다(self) -> None:
        profile = {
            "current_balance": 9_000_000,
            "emergency_fund_balance": 2_000_000,
            "expected_card_payment_amount": 100_000,
            "days_until_card_due": 5,
            "savebox_balance": 1_800_000,
            "available_fixed_expense": 300_000,
            "available_fixed_income": 2_500_000,
            "monthly_spending_30d": 1_100_000,
        }

        payload = _analyzer(finance_profile=profile).analyze_crawl_result(_crawl())

        self.assertEqual(payload["input_contract"]["default_fallback_rate"], 0.0)
        self.assertEqual(payload["finance_profile"]["current_balance"], 9_000_000.0)
        self.assertEqual(payload["finance_profile"]["savebox_balance"], 1_800_000.0)

    def test_ResolvedFinanceProfile을_주면_출처가_보존된다(self) -> None:
        resolved = resolve_finance_profile(
            {
                "current_balance": RawField(1),
                "emergency_fund_balance": RawField(1),
                "expected_card_payment_amount": RawField(1),
                "days_until_card_due": RawField(14, is_default=True),
            }
        )

        payload = _analyzer(finance_profile=resolved).analyze_crawl_result(_crawl())

        origins = payload["input_contract"]["origins"]
        self.assertEqual(origins["days_until_card_due"], Origin.DEFAULT)
        self.assertEqual(origins["current_balance"], Origin.UPSTREAM)

    def test_모르는_키가_들어오면_생성_시점에_거부한다(self) -> None:
        """필드명 오타(balance 대 current_balance)가 조용히 무시되던 문제."""
        with self.assertRaises(InputContractViolation) as ctx:
            _analyzer(finance_profile={"balance": 300_000})

        self.assertEqual(ctx.exception.violations[0].code, "unknown_field")

    def test_깨진_값은_생성_시점에_거부한다(self) -> None:
        with self.assertRaises(InputContractViolation):
            _analyzer(finance_profile={"current_balance": "abc"})

    def test_캠멜케이스_키는_거부한다(self) -> None:
        """finance_profile.py 의 _FIELD_ALIASES 가 흡수하던 불일치.
        별칭 처리가 사라진 뒤에는 불일치가 조용히 넘어가지 않고 드러나야 한다."""
        with self.assertRaises(InputContractViolation):
            _analyzer(finance_profile={"currentBalance": 300_000})


class MonthlySpendingIsNotProductHistoryTest(unittest.TestCase):
    """월 지출이 크롤링한 상품 가격 이력과 무관함을 고정한다.

    예전에는 `상품 평균가 x 건수`로 계산해서, 같은 상품을 보는 모든 사용자가 같은
    월 지출을 갖고 사용자의 실제 소비는 반영되지 않았다.
    """

    @staticmethod
    def _scores(monthly: int, window_stats: dict | None) -> dict[str, float]:
        analyzer = _analyzer(
            finance_profile={
                "current_balance": 5_000_000,
                "emergency_fund_balance": 1_000_000,
                "expected_card_payment_amount": 100_000,
                "days_until_card_due": 10,
                "monthly_spending_30d": monthly,
            }
        )
        features = {"price_int": 1_000_000, "missing_fields": []}
        return analyzer._build_feature_scores(features, window_stats=window_stats)

    def test_크롤링_이력이_달라도_월_지출_기반_피처는_같다(self) -> None:
        cheap_history = {"30d": {"avg_price": 10_000, "count": 3}}
        pricey_history = {"30d": {"avg_price": 900_000, "count": 30}}

        a = self._scores(1_000_000, cheap_history)
        b = self._scores(1_000_000, pricey_history)

        self.assertEqual(
            a["product_price_vs_monthly_spending"],
            b["product_price_vs_monthly_spending"],
        )
        self.assertEqual(a["emergency_fund_balance"], b["emergency_fund_balance"])

    def test_사용자의_월_지출이_달라지면_피처가_달라진다(self) -> None:
        low = self._scores(500_000, None)
        high = self._scores(2_000_000, None)

        # 같은 가격이라도 월 지출이 작을수록 부담이 크다.
        self.assertGreater(
            low["product_price_vs_monthly_spending"],
            high["product_price_vs_monthly_spending"],
        )
        self.assertAlmostEqual(low["product_price_vs_monthly_spending"], 2.0)
        self.assertAlmostEqual(high["product_price_vs_monthly_spending"], 0.5)


class NoFabricatedExplanationTest(unittest.TestCase):
    """설명(SHAP)을 넘기지 않는 경로(CLI/진단)가 가짜 SHAP 값을 지어내지 않는다.

    예전에는 판단 점수에 `sum(x)` 라는 가짜 모델의 SHAP 을 씌워 점수 x 0.25 를 '기여도'로 보여 줬다.
    """

    def test_요인_점수는_판단_점수_그대로이고_엔진_상태는_설명을_만들지_않았다고_말한다(self) -> None:
        analyzer = _analyzer()
        payload = analyzer.analyze_crawl_result(_crawl(), top_k=4)

        state = payload["runtime_engines"]["shap"]
        self.assertEqual((state["enabled"], state["backend"]), (False, "feature_score_ranking"))
        self.assertEqual(state["reason"], "finance_explanation_not_provided")
        expected = analyzer._build_feature_scores({"price_int": 1_200_000, "missing_fields": []}, window_stats=None)
        reasons = payload["crawl"]["items"][0]["reasons"]
        self.assertTrue(reasons)
        for reason in reasons:
            self.assertAlmostEqual(reason["score"], expected[reason["feature"]], places=9, msg=reason["feature"])


class SingleSourceOfTruthTest(unittest.TestCase):
    """기본값 숫자가 analyzer 에 다시 복붙되지 않도록 소스 수준에서 막는다.

    이전에는 같은 값(1_500_000, 600_000, 200_000, 14)이 analyzer.py 안에
    세 군데 복붙돼 있었고, 한 곳만 고치면 서로 어긋났다.
    """

    def test_analyzer에_재무_기본값_리터럴이_없다(self) -> None:
        source = ANALYZER_SOURCE.read_text(encoding="utf-8")

        for literal in ("1_500_000", "600_000", "200_000", "1500000"):
            self.assertNotIn(literal, source, f"기본값 {literal} 이 analyzer 에 있습니다")

    def test_analyzer는_프로필을_get_기본값으로_읽지_않는다(self) -> None:
        source = ANALYZER_SOURCE.read_text(encoding="utf-8")

        offenders = re.findall(r"_finance_profile\.get\(", source)
        self.assertEqual(offenders, [], "프로필은 계약을 통과했으므로 직접 인덱싱해야 합니다")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
