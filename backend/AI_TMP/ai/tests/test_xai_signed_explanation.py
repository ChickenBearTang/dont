"""부호 있는 설명이 분석기와 운영 경로(service)에서 끝까지 이어지는지 확인한다.

핵심 약속: 화면에 나가는 문구의 방향 = 점수의 방향 = 사용자의 실제 상황.
예전에는 형편이 좋은 사용자에게도 "비상자금이 부족합니다"가 나갔다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore
from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest
from domain.xai_purchase.service import evaluate_pr_purchase_xai

from ..finance_engine.explain import EXPLANATION_GROUPS
from ..models import CrawlResult, HotDeal
from ..xai.analyzer import ExplainabilityAnalyzer
from ..xai.counterfactuals import CounterfactualEngine
from ..xai.purchase_core.reasons import REASON_CODE_MAP, REASON_TEXT, SIGNED_REASON_TEXT


def _crawl(price: str = "100,000") -> CrawlResult:
    return CrawlResult(
        source="test",
        fetched_at=datetime.now(timezone.utc),
        items=[HotDeal(title="x", url="https://example.com/x", price=price)],
    )


FINANCE = {
    "current_balance": 1_000_000, "emergency_fund_balance": 500_000, "savebox_balance": 400_000,
    "expected_card_payment_amount": 100_000, "days_until_card_due": 10, "monthly_spending_30d": 1_000_000,
}


def _reasons(payload: dict) -> list[dict]:
    return payload["crawl"]["items"][0]["reasons"]


class AnalyzerSignedModeTest(unittest.TestCase):
    def _analyze(self, explanation, *, top_k=3, window_stats=None, price_signal=None, state=None):
        analyzer = ExplainabilityAnalyzer(
            finance_profile=FINANCE,
            dice_counterfactual_engine=CounterfactualEngine(),  # DiCE 는 수십 초 걸려 이 테스트와 무관하다
            finance_explanation=explanation,
            finance_explanation_state=state,
            price_model_signal=price_signal,
        )
        return analyzer.analyze_crawl_result(_crawl(), top_k=top_k, window_stats=window_stats)

    def test_불리한_재무_요인은_음수_방향과_불리한_문구로_나간다(self) -> None:
        payload = self._analyze({"emergency_fund_balance": -2.0, "days_until_card_due": -0.5})

        by_feature = {r["feature"]: r for r in _reasons(payload)}
        self.assertEqual(by_feature["emergency_fund_balance"]["impact_direction"], "negative")
        self.assertEqual(by_feature["emergency_fund_balance"]["reason_text"], REASON_TEXT["EMERGENCY_FUND_TOO_LOW"])

    def test_유리한_재무_요인은_양수_방향과_유리한_문구로_나간다(self) -> None:
        payload = self._analyze({"emergency_fund_balance": 1.2})

        reason = _reasons(payload)[0]
        self.assertEqual(reason["impact_direction"], "positive")
        self.assertEqual(reason["reason_text"], SIGNED_REASON_TEXT["EMERGENCY_FUND_TOO_LOW"][0])
        self.assertNotEqual(reason["reason_text"], REASON_TEXT["EMERGENCY_FUND_TOO_LOW"])

    def test_재무_요인은_영향이_큰_순서로_나간다(self) -> None:
        payload = self._analyze(
            {"emergency_fund_balance": -0.3, "days_until_card_due": 2.5, "projected_balance_after_purchase": -1.1},
            top_k=3,
        )

        self.assertEqual(
            [r["feature"] for r in _reasons(payload)],
            ["days_until_card_due", "projected_balance_after_purchase", "emergency_fund_balance"],
        )

    def test_가격_요인에는_최대_top_k_빼기_2개_자리를_준다(self) -> None:
        payload = self._analyze(
            {"emergency_fund_balance": -2.0, "days_until_card_due": -1.5, "projected_balance_after_purchase": -1.0},
            top_k=3,
            window_stats={"30d": {"avg_price": 200_000}},  # 현재 100,000 -> 싸다
            price_signal={"price_model_gap_score": -0.8},
        )

        features = [r["feature"] for r in _reasons(payload)]
        self.assertEqual(len(features), 3)
        self.assertEqual(sum(1 for f in features if f in EXPLANATION_GROUPS), 2)
        self.assertEqual(sum(1 for f in features if f in ("avg_price_30d", "price_model_gap_score")), 1)

    def test_평균가보다_싸면_가격_요인이_유리하게_나간다(self) -> None:
        payload = self._analyze(
            {}, top_k=1, window_stats={"30d": {"avg_price": 200_000}}  # 100,000 / 200,000 = 0.5
        )

        reason = _reasons(payload)[0]
        self.assertEqual(reason["feature"], "avg_price_30d")
        self.assertEqual(reason["impact_direction"], "positive")
        self.assertAlmostEqual(reason["score"], 0.5)
        self.assertIn("낮", reason["reason_text"])

    def test_평균가보다_비싸면_가격_요인이_불리하게_나간다(self) -> None:
        payload = self._analyze({}, top_k=1, window_stats={"30d": {"avg_price": 50_000}})

        reason = _reasons(payload)[0]
        self.assertEqual(reason["impact_direction"], "negative")
        self.assertIn("높게", reason["reason_text"])

    def test_평균가와_비슷하면_가격_요인을_자리에서_뺀다(self) -> None:
        payload = self._analyze(
            {"emergency_fund_balance": -1.0}, top_k=3, window_stats={"30d": {"avg_price": 100_000}}
        )

        self.assertNotIn("avg_price_30d", [r["feature"] for r in _reasons(payload)])

    def test_설명이_비어_있으면_재무_요인을_가짜로_채우지_않는다(self) -> None:
        payload = self._analyze({}, top_k=3, window_stats={"30d": {"avg_price": 200_000}})

        features = [r["feature"] for r in _reasons(payload)]
        self.assertFalse(set(features) & set(EXPLANATION_GROUPS))
        self.assertEqual(payload["runtime_engines"]["shap"]["enabled"], False)
        self.assertEqual(payload["runtime_engines"]["shap"]["reason"], "finance_explanation_unavailable")

    def test_실제_SHAP이_있으면_상태에_shap_tree가_기록된다(self) -> None:
        payload = self._analyze(
            {"emergency_fund_balance": -1.0},
            state={"enabled": True, "backend": "shap_tree", "feature_count": 10},
        )

        shap_state = payload["runtime_engines"]["shap"]
        self.assertTrue(shap_state["enabled"])
        self.assertEqual(shap_state["backend"], "shap_tree")

    def test_판단은_설명_모드와_무관하게_같다(self) -> None:
        """설명을 바꿔도 구매 판단(규칙 엔진)은 건드리지 않는다."""
        legacy = ExplainabilityAnalyzer(
            finance_profile=FINANCE, dice_counterfactual_engine=CounterfactualEngine()
        ).analyze_crawl_result(_crawl())
        signed = self._analyze({"emergency_fund_balance": -3.0, "days_until_card_due": -3.0})

        self.assertEqual(
            legacy["crawl"]["items"][0]["decision"], signed["crawl"]["items"][0]["decision"]
        )

    def test_설명_모드를_주지_않으면_예전_방식이다(self) -> None:
        payload = ExplainabilityAnalyzer(
            finance_profile=FINANCE, dice_counterfactual_engine=CounterfactualEngine()
        ).analyze_crawl_result(_crawl())

        self.assertEqual(payload["runtime_engines"]["shap"]["backend"], "shap_fast")


def _request(*, price: int, finance: dict) -> PurchaseXaiEvaluationRequest:
    def pv(value):
        return {"value": value, "source": "t", "snapshotId": "s", "isDefault": False, "isEstimated": False}

    return PurchaseXaiEvaluationRequest.model_validate(
        {
            "requestId": "r", "schemaVersion": "v1", "contextVersion": "v1",
            "purchase": {
                "postId": 1, "title": "t", "itemName": "item", "content": "c", "category": "IT",
                "purchaseUrl": None, "priceAmount": pv(price),
            },
            "financeProfile": {
                "currentBalance": pv(finance["current_balance"]),
                "emergencyFundBalance": pv(finance["emergency_fund_balance"]),
                "expectedCardPaymentAmount": pv(finance["expected_card_payment_amount"]),
                "daysUntilCardDue": pv(finance["days_until_card_due"]),
                "saveboxBalance": pv(finance["savebox_balance"]),
            },
            "recentTransactions": [],
        }
    )


TIGHT = dict(
    current_balance=900_000, emergency_fund_balance=150_000, savebox_balance=150_000,
    expected_card_payment_amount=700_000, days_until_card_due=2,
)
HEALTHY = dict(
    current_balance=8_000_000, emergency_fund_balance=3_000_000, savebox_balance=2_500_000,
    expected_card_payment_amount=300_000, days_until_card_due=20,
)


class ServiceEndToEndTest(unittest.TestCase):
    def _evaluate(self, request, *, env=None):
        env = env or {}
        with tempfile.TemporaryDirectory() as tmp, patch(
            "domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(Path(tmp) / "a.jsonl")
        ), patch.dict("os.environ", env):
            return evaluate_pr_purchase_xai(request)

    @staticmethod
    def _finance_factors(response):
        codes = {REASON_CODE_MAP[g][0] for g in EXPLANATION_GROUPS}
        return [f for f in response.top_factors if f.code in codes]

    def test_빠듯한_사용자의_재무_요인은_전부_불리하고_불리한_문구다(self) -> None:
        response = self._evaluate(_request(price=2_500_000, finance=TIGHT))

        factors = self._finance_factors(response)
        self.assertGreaterEqual(len(factors), 1)
        for factor in factors:
            self.assertEqual(factor.direction, "negative", factor.code)
            self.assertEqual(factor.label, REASON_TEXT[factor.code])
        self.assertEqual(response.runtime_engines.shap, "shap_tree")

    def test_여유_있는_사용자에게_부족하다는_문구가_나가지_않는다(self) -> None:
        """이 테스트가 예전 버그를 직접 잡는다."""
        response = self._evaluate(_request(price=89_000, finance=HEALTHY))

        factors = self._finance_factors(response)
        self.assertGreaterEqual(len(factors), 1)
        for factor in factors:
            self.assertEqual(factor.direction, "positive", factor.code)
            self.assertEqual(factor.label, SIGNED_REASON_TEXT[factor.code][0])
            self.assertNotEqual(factor.label, REASON_TEXT[factor.code])
        labels = " ".join(f.label for f in response.top_factors)
        self.assertNotIn("부족합니다", labels)

    def test_모든_요인의_문구가_방향과_일치한다(self) -> None:
        for name, case in (("tight", (2_500_000, TIGHT)), ("healthy", (89_000, HEALTHY))):
            with self.subTest(case=name):
                response = self._evaluate(_request(price=case[0], finance=case[1]))
                for factor in response.top_factors:
                    texts = SIGNED_REASON_TEXT.get(factor.code)
                    if texts is None:
                        continue
                    expected = {"positive": texts[0], "negative": texts[1]}[factor.direction]
                    self.assertIn(factor.label, {expected, texts[2]}, factor.code)

    def test_SHAP을_끄면_재무_요인을_빼고_이유를_경고한다(self) -> None:
        response = self._evaluate(
            _request(price=2_500_000, finance=TIGHT), env={"AI_XAI_SHAP_ENABLED": "0"}
        )

        self.assertEqual(self._finance_factors(response), [])
        self.assertIn("FINANCE_EXPLANATION_UNAVAILABLE:shap_disabled_by_config", response.warnings)

    def test_재무_모델을_읽지_못하면_설명도_시도하지_않고_이유를_경고한다(self) -> None:
        """서비스는 enabled=True 를 명시하므로 환경변수로는 끌 수 없다. 모델 파일을
        못 읽는 상황을 직접 주입한다."""
        unavailable = ({}, {"enabled": False, "backend": "fallback", "reason": "model_path_missing"})
        with patch("domain.xai_purchase.service.predict_finance_signal", return_value=unavailable), patch(
            "domain.xai_purchase.service.explain_finance_signal"
        ) as explain:
            response = self._evaluate(_request(price=2_500_000, finance=TIGHT))

        explain.assert_not_called()  # 설명할 모델이 없으면 시도하지 않는다
        self.assertEqual(self._finance_factors(response), [])
        self.assertIn(
            "FINANCE_EXPLANATION_UNAVAILABLE:finance_model_model_path_missing", response.warnings
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
