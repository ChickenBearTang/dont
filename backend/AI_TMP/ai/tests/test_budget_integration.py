"""5·3·2 예산 규칙이 분석기/설명/반사실/서비스까지 이어지는지 확인한다.

앞단(Spring)이 월 소득과 고정지출을 보내면 판단과 설명에 반영되고, 보내지 않으면(지금 상태)
예전과 똑같이 동작하며 '예산 판단 불가'를 숨기지 않고 알린다.
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

from ..models import CrawlResult, HotDeal
from ..xai.analyzer import ExplainabilityAnalyzer
from ..xai.counterfactuals import CounterfactualEngine
from ..xai.input_contract import RawField, resolve_finance_profile
from ..xai.purchase_core.reasons import BUDGET_STATUS_REASON_TEXT, REASON_CODE_MAP

URL = "https://example.com/x"
PROFILE = {
    "current_balance": 3_000_000, "emergency_fund_balance": 3_000_000, "savebox_balance": 1_000_000,
    "expected_card_payment_amount": 200_000, "days_until_card_due": 20, "monthly_spending_30d": 400_000,
    "available_fixed_income": 3_000_000, "available_fixed_expense": 900_000,
}


def resolved(**override):
    values = {**PROFILE, **override}
    raw = {k: (None if v is None else RawField(v)) for k, v in values.items()}
    return resolve_finance_profile(raw, strict=True)


def crawl(price: int):
    return CrawlResult(
        source="t", fetched_at=datetime.now(timezone.utc),
        items=[HotDeal(title="x", url=URL, price=f"{price:,}")],
    )


def analyzer(profile, **kw):
    return ExplainabilityAnalyzer(
        finance_profile=profile, dice_counterfactual_engine=CounterfactualEngine(),
        finance_model_signal={"finance_model_risk_score": -0.6, "finance_model_affordability_score": 0.6}, **kw,
    )


class FeatureScoresTest(unittest.TestCase):
    def _scores(self, profile, price=100_000):
        a = analyzer(profile)
        return a._build_feature_scores({"price_int": price, "missing_fields": []}, window_stats=None)

    def test_소득과_고정지출이_실제_값이면_예산_사용률이_점수표에_들어간다(self) -> None:
        scores = self._scores(resolved())

        self.assertAlmostEqual(scores["budget_ratio_before"], (900_000 + 400_000) / 1_500_000)
        self.assertAlmostEqual(scores["budget_ratio_after"], (900_000 + 400_000 + 100_000) / 1_500_000)

    def test_소득이_기본값으로_채워진_경우에는_예산을_판단하지_않는다(self) -> None:
        profile = resolved(available_fixed_income=None)  # 필수 아님 -> 기본값 100만 원, 출처 DEFAULT

        scores = self._scores(profile)

        self.assertNotIn("budget_ratio_after", scores)

    def test_고정지출이_기본값이면_판단하지_않는다(self) -> None:
        self.assertNotIn("budget_ratio_after", self._scores(resolved(available_fixed_expense=None)))

    def test_월_지출이_기본값이면_판단하지_않는다(self) -> None:
        """거래가 없어 월 지출을 모르면 기본값 80만 원으로 사용률을 만들지 않는다."""
        self.assertNotIn("budget_ratio_after", self._scores(resolved(monthly_spending_30d=None)))

    def test_dict_프로필에_소득_키가_없으면_판단하지_않는다(self) -> None:
        """예전 호출부(CLI, 진단)는 5개 재무 키만 넘긴다. 나머지는 기본값이라 예산 판단을 하지 않는다."""
        legacy = {k: v for k, v in PROFILE.items()
                  if k not in {"available_fixed_income", "available_fixed_expense", "monthly_spending_30d"}}

        self.assertNotIn("budget_ratio_after", self._scores(legacy))

    def test_dict_프로필에_값이_다_있으면_판단한다(self) -> None:
        self.assertIn("budget_ratio_after", self._scores(dict(PROFILE)))

    def test_추정값도_판단에_쓴다(self) -> None:
        raw = {k: RawField(v) for k, v in PROFILE.items() if k != "monthly_spending_30d"}
        raw["monthly_spending_30d"] = RawField(400_000, is_estimated=True)

        scores = self._scores(resolve_finance_profile(raw, strict=True))

        self.assertIn("budget_ratio_after", scores)


class AnalyzeTest(unittest.TestCase):
    def _item(self, profile, price, **kw):
        payload = analyzer(profile, **kw).analyze_crawl_result(crawl(price))
        return payload, payload["crawl"]["items"][0]

    def test_한도를_넘기는_가격은_구매_비추천이다(self) -> None:
        # 한도 150만, 사용 130만 -> 가격 30만이면 160만
        payload, item = self._item(resolved(), 300_000)

        self.assertEqual(item["decision"], "NOT_RECOMMENDED")
        self.assertIn("BUDGET_ZONE_EXCEEDED", payload["audit_logs"][0]["fired_rule_ids"])

    def test_여유_있는_가격은_바로_구매다(self) -> None:
        payload, item = self._item(resolved(), 50_000)

        self.assertEqual(item["decision"], "BUY_NOW")
        self.assertIn("BUDGET_WITHIN_AND_AFFORDABLE", payload["audit_logs"][0]["fired_rule_ids"])

    def test_페이로드에_예산_평가가_담긴다(self) -> None:
        payload, _ = self._item(resolved(), 300_000)

        self.assertEqual(payload["budgets"][URL]["status"], "over")
        self.assertEqual(payload["budgets"][URL]["overshoot"], 100_000.0)

    def test_소득을_모르면_예산_판단_불가를_사유와_함께_담는다(self) -> None:
        payload, _ = self._item(resolved(available_fixed_income=None), 300_000)

        self.assertEqual(payload["budgets"][URL]["status"], "unavailable")
        self.assertEqual(payload["budgets"][URL]["reason"], "income_not_provided_by_upstream")

    def test_소득을_모르면_판단은_예산_규칙_없이_예전과_같다(self) -> None:
        _, with_income = self._item(resolved(), 50_000)
        _, without = self._item(resolved(available_fixed_income=None), 50_000)

        self.assertEqual(with_income["decision"], "BUY_NOW")
        self.assertNotEqual(without["decision"], "BUY_NOW")  # 예산 근거가 없으면 이 규칙으로는 올리지 않는다


class ExplanationTest(unittest.TestCase):
    def _reasons(self, price, profile=None):
        a = analyzer(
            profile or resolved(),
            finance_explanation={"emergency_fund_balance": 0.5, "days_until_card_due": 0.4},
            finance_explanation_state={"enabled": True, "backend": "shap_tree"},
        )
        return a.analyze_crawl_result(crawl(price), top_k=4)["crawl"]["items"][0]["reasons"]

    def test_예산_사유_코드와_상태별_문구가_있다(self) -> None:
        self.assertEqual(REASON_CODE_MAP["budget_zone_usage"][0], "BUDGET_ZONE_USAGE")
        self.assertEqual(set(BUDGET_STATUS_REASON_TEXT), {"within", "tight", "over", "already_over"})
        self.assertEqual(len(set(BUDGET_STATUS_REASON_TEXT.values())), 4)

    def test_초과면_불리한_문구로_나간다(self) -> None:
        reason = next(r for r in self._reasons(300_000) if r["feature"] == "budget_zone_usage")

        self.assertEqual(reason["impact_direction"], "negative")
        self.assertEqual(reason["reason_text"], BUDGET_STATUS_REASON_TEXT["over"])

    def test_여유가_있으면_유리한_문구로_나간다(self) -> None:
        reason = next(r for r in self._reasons(30_000) if r["feature"] == "budget_zone_usage")

        self.assertEqual(reason["impact_direction"], "positive")
        self.assertEqual(reason["reason_text"], BUDGET_STATUS_REASON_TEXT["within"])

    def test_예산을_모르면_예산_사유는_나오지_않는다(self) -> None:
        reasons = self._reasons(300_000, resolved(available_fixed_income=None))

        self.assertNotIn("budget_zone_usage", [r["feature"] for r in reasons])


class ReasonOrderTest(unittest.TestCase):
    def _reasons(self, price, **kw):
        a = analyzer(resolved(), **kw)
        return a.analyze_crawl_result(crawl(price), top_k=3)["crawl"]["items"][0]["reasons"]

    SHAP = {
        "finance_explanation": {"emergency_fund_balance": 0.5, "days_until_card_due": 0.4},
        "finance_explanation_state": {"enabled": True, "backend": "shap_tree"},
    }

    def test_한도를_넘기면_예산_사유가_맨_앞이다(self) -> None:
        self.assertEqual(self._reasons(300_000, **self.SHAP)[0]["feature"], "budget_zone_usage")

    def test_빠듯하면_예산_사유가_맨_앞이고_문구가_빠듯함이다(self) -> None:
        first = self._reasons(100_000, **self.SHAP)[0]  # (130+10)/150 = 93%
        self.assertEqual(first["feature"], "budget_zone_usage")
        self.assertEqual(first["reason_text"], BUDGET_STATUS_REASON_TEXT["tight"])
        self.assertEqual(first["impact_direction"], "negative")

    def test_여유가_있으면_예산_사유는_맨_뒤다(self) -> None:
        reasons = self._reasons(30_000, **self.SHAP)
        self.assertEqual(reasons[-1]["feature"], "budget_zone_usage")
        self.assertNotEqual(reasons[0]["feature"], "budget_zone_usage")

    def test_예산_사유는_top_k_에_더해진다(self) -> None:
        with_budget = self._reasons(300_000, **self.SHAP)
        without = [r for r in with_budget if r["feature"] != "budget_zone_usage"]
        self.assertEqual(len(with_budget), len(without) + 1)

    def test_SHAP_이_없는_경로에서도_입력용_점수가_요인으로_새지_않는다(self) -> None:
        """budget_ratio_* 는 규칙 입력이다. 요인/근거 목록에는 budget_zone_usage 만 나와야 한다."""
        item = analyzer(resolved()).analyze_crawl_result(crawl(300_000), top_k=4)["crawl"]["items"][0]

        features = {e["feature"] for e in item["supporting_evidence"]}
        self.assertIn("budget_zone_usage", features)
        self.assertFalse({f for f in features if f.startswith("budget_ratio_")})
        self.assertNotIn("DECISION_FEATURE_SIGNAL", [r["reason_code"] for r in item["reasons"] if r["feature"].startswith("budget")])
        self.assertEqual(item["reasons"][0]["feature"], "budget_zone_usage")


class CounterfactualTest(unittest.TestCase):
    def test_초과면_가격을_낮추라는_검증된_제안이_나온다(self) -> None:
        def signals(price, profile):
            return {}, {"finance_model_risk_score": -0.6, "finance_model_affordability_score": 0.6}

        a = ExplainabilityAnalyzer(
            finance_profile=resolved(), dice_counterfactual_engine=CounterfactualEngine(), scenario_signals=signals,
            finance_model_signal={"finance_model_risk_score": -0.6, "finance_model_affordability_score": 0.6},
        )
        item = a.analyze_crawl_result(crawl(300_000))["crawl"]["items"][0]

        price_cf = [c for c in item["counterfactuals"] if c["variable"] == "product_price"]
        self.assertTrue(price_cf, item["counterfactuals"])
        self.assertTrue(price_cf[0]["validated"])
        # 제안된 가격에서 실제로 한도 안(판단이 나아짐)이어야 한다
        self.assertLessEqual(price_cf[0]["threshold"], 200_000)  # 한도 150만 - 사용 130만 = 여유 20만 이하


def request(price, finance_extra=None):
    def pv(value):
        return {"value": value, "source": "t", "snapshotId": "s", "isDefault": False, "isEstimated": False}

    finance = {
        "currentBalance": pv(3_000_000), "emergencyFundBalance": pv(3_000_000), "expectedCardPaymentAmount": pv(200_000),
        "daysUntilCardDue": pv(20), "saveboxBalance": pv(1_000_000),
    }
    finance.update(finance_extra or {})
    return PurchaseXaiEvaluationRequest.model_validate({
        "requestId": "r", "schemaVersion": "v1", "contextVersion": "v1",
        "purchase": {"postId": 1, "title": "t", "itemName": "i", "content": "c", "category": "IT", "purchaseUrl": None,
                     "priceAmount": pv(price)},
        "financeProfile": finance,
        "recentTransactions": [{
            "transactionDate": datetime.now(timezone.utc).strftime("%Y%m%d"), "transactionTime": "120000",
            "merchantName": "m", "categoryName": "c", "transactionAmount": 400_000,
        }],
    })


def evaluate(req):
    with tempfile.TemporaryDirectory() as tmp, patch(
        "domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(Path(tmp) / "a.jsonl")
    ):
        return evaluate_pr_purchase_xai(req)


WITH_INCOME = {"availableFixedIncome": {"value": 3_000_000, "source": "s", "snapshotId": "s"},
               "availableFixedExpense": {"value": 900_000, "source": "s", "snapshotId": "s"}}


class ServiceTest(unittest.TestCase):
    def test_소득이_오면_예산_지표와_판단이_응답에_나온다(self) -> None:
        response = evaluate(request(300_000, WITH_INCOME))

        self.assertEqual(response.decision, "NOT_RECOMMENDED")
        metrics = {m.code: m.value for m in response.financial_evaluation.key_metrics}
        self.assertIn("budget_zone_limit", metrics)
        self.assertEqual(metrics["budget_zone_limit"], "1,500,000원")
        self.assertIn("budget_zone_used_after", metrics)
        self.assertIn("107%", metrics["budget_zone_used_after"])  # 160만 / 150만
        codes = [f.code for f in response.top_factors]
        self.assertIn("BUDGET_ZONE_USAGE", codes)

    def test_소득이_안_오면_예산_판단_불가_경고가_나오고_가짜_고정수입을_보여주지_않는다(self) -> None:
        response = evaluate(request(300_000))

        self.assertIn("BUDGET_RULE_UNAVAILABLE:income_not_provided_by_upstream", response.warnings)
        metrics = {m.code for m in response.financial_evaluation.key_metrics}
        self.assertNotIn("budget_zone_limit", metrics)
        self.assertNotIn("available_fixed_income", metrics)  # 예전에는 기본값 1,000,000원을 사실처럼 보여줬다
        self.assertNotIn("available_fixed_expense", metrics)

    def test_소득이_오면_고정수입_지표는_실제_값으로_나온다(self) -> None:
        metrics = {m.code: m.value for m in evaluate(request(50_000, WITH_INCOME)).financial_evaluation.key_metrics}

        self.assertEqual(metrics["available_fixed_income"], "3,000,000원")
        self.assertEqual(metrics["available_fixed_expense"], "900,000원")

    def test_비상금이_석_달치_미만이면_경고한다(self) -> None:
        # 지출 130만, 비상금 300만 -> 2.3개월
        response = evaluate(request(50_000, WITH_INCOME))

        self.assertIn("EMERGENCY_COVER_LOW", response.warnings)

    def test_비상금이_충분하면_경고하지_않는다(self) -> None:
        extra = {**WITH_INCOME, "emergencyFundBalance": {"value": 9_000_000, "source": "s", "snapshotId": "s"}}

        self.assertNotIn("EMERGENCY_COVER_LOW", evaluate(request(50_000, extra)).warnings)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
