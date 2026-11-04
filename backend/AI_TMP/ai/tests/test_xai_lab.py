"""XAI 랩 API/페이지 테스트."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient

from consumption_poc.main import app
from domain.xai_lab import service
from domain.xai_purchase.audit_store import JsonlXaiAuditLogStore

PAGE = Path(__file__).resolve().parents[1] / "frontend" / "xai-lab.html"
BASE = "/api/v1/xai-lab"
INPUT = dict(price=2_500_000, current_balance=900_000, emergency_fund_balance=150_000, savebox_balance=150_000,
             expected_card_payment_amount=700_000, days_until_card_due=2, monthly_spending_30d=1_300_000)
# 한도 150만 원(소득 300만 원의 50%), 구매 전 사용 130만 원 (고정지출 90만 + 최근 30일 40만)
BUDGET = dict(monthly_income=3_000_000, fixed_expense=900_000)
HEALTHY = dict(price=89_000, current_balance=8_000_000, emergency_fund_balance=3_000_000, savebox_balance=2_500_000,
               expected_card_payment_amount=300_000, days_until_card_due=20, monthly_spending_30d=1_400_000)


def client():
    return TestClient(app)


class DisabledByDefaultTest(unittest.TestCase):
    def test_환경변수가_없으면_페이지와_API가_모두_404다(self) -> None:
        with patch.dict("os.environ", {"AI_XAI_LAB_ENABLED": ""}):
            c = client()
            for method, url in [("get", "/xai-lab"), ("get", f"{BASE}/overview"), ("get", f"{BASE}/validation"),
                                ("get", f"{BASE}/distributions"), ("get", f"{BASE}/evaluation"),
                                ("post", f"{BASE}/inspect"), ("post", f"{BASE}/simulate")]:
                with self.subTest(url=url):
                    response = getattr(c, method)(url, **({"json": INPUT} if method == "post" else {}))
                    self.assertEqual(response.status_code, 404)

    def test_여러_표기로_켤_수_있다(self) -> None:
        for value in ("1", "true", "YES", "on"):
            with self.subTest(value=value), patch.dict("os.environ", {"AI_XAI_LAB_ENABLED": value}):
                self.assertEqual(client().get("/xai-lab").status_code, 200)


class EnabledApiTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.dict("os.environ", {"AI_XAI_LAB_ENABLED": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.c = client()

    def test_모델_지도는_가격_모델이_차단됐다고_말한다(self) -> None:
        data = self.c.get(f"{BASE}/overview").json()

        nodes = {n["id"]: n for n in data["nodes"]}
        self.assertEqual(nodes["price_model"]["status"], "blocked")
        self.assertIn("TARGET_IN_FEATURES", nodes["price_model"]["trust"]["reasons"])
        self.assertEqual(nodes["finance_model"]["status"], "synthetic")
        self.assertEqual(nodes["finance_model"]["data_source"]["label_source"], "synthetic_rule")
        self.assertIn("규칙을 얼마나 따라 하나", nodes["finance_model"]["caveat"])

    def test_모델_지도의_간선은_모두_존재하는_노드를_잇는다(self) -> None:
        data = self.c.get(f"{BASE}/overview").json()

        ids = {n["id"] for n in data["nodes"]}
        self.assertTrue(data["edges"])
        for a, b in data["edges"]:
            self.assertIn(a, ids)
            self.assertIn(b, ids)

    def test_재무_모델_입력은_원본과_모델_안_계산으로_구분된다(self) -> None:
        nodes = {n["id"]: n for n in self.c.get(f"{BASE}/overview").json()["nodes"]}

        kinds = {f["name"]: f["kind"] for f in nodes["finance_model"]["features"]}
        self.assertEqual(len(kinds), 10)
        self.assertEqual(sum(1 for k in kinds.values() if k == "입력"), 7)
        self.assertEqual(kinds["product_price_vs_monthly_spending"], "모델 안에서 계산")

    def test_SHAP_노드는_4개_묶음과_구성_열을_보여준다(self) -> None:
        nodes = {n["id"]: n for n in self.c.get(f"{BASE}/overview").json()["nodes"]}

        groups = nodes["shap"]["groups"]
        self.assertEqual(len(groups), 4)
        members = [m for g in groups for m in g["members"]]
        self.assertEqual(len(members), 10)

    def test_데이터_검증은_가격_학습_데이터의_오염을_보여준다(self) -> None:
        data = self.c.get(f"{BASE}/validation").json()

        reports = {r["name"]: r for r in data["reports"]}
        price = reports["price_training_rows"]
        self.assertFalse(price["ok"])
        self.assertEqual(price["counts_by_code"]["BRAND_IS_PRODUCT_ID"], 67)
        self.assertFalse(reports["training_setup"]["ok"])
        self.assertTrue(reports["finance_rows"]["ok"])
        self.assertFalse(data["price_artifact_verdict"]["trusted"])

    def test_검증_응답은_코드별_대표_사례만_담아_작다(self) -> None:
        data = self.c.get(f"{BASE}/validation").json()

        for report in data["reports"]:
            for issue in report["issues"]:
                self.assertLessEqual(len(issue["samples"]), 3)

    def test_분포는_유형별에서_월_지출과_잔액이_함께_움직인다(self) -> None:
        data = self.c.get(f"{BASE}/distributions").json()

        corr = data["log_corr_monthly_vs_balance"]
        self.assertLess(abs(corr["uniform"]), 0.1)
        self.assertGreater(corr["persona"], 0.5)
        for h in data["histograms"].values():
            self.assertEqual(len(h["edges"]), len(h["share"]["uniform"]) + 1)
            for series in h["share"].values():
                self.assertLessEqual(sum(series), 1.0001)
        self.assertIn("가정값", data["note"])

    def test_성능_스냅샷이_있으면_유형별_점수를_준다(self) -> None:
        data = self.c.get(f"{BASE}/evaluation").json()

        self.assertTrue(data["available"])
        self.assertIn("정확도가 아니다", data["disclaimer"])
        self.assertIn("lightgbm/mixed", data["by_persona"]["candidates"])

    def test_성능_스냅샷이_없으면_만드는_방법을_알려준다(self) -> None:
        with patch.object(service, "SNAPSHOT_PATH", Path("/no/such/snapshot.json")):
            data = self.c.get(f"{BASE}/evaluation").json()

        self.assertFalse(data["available"])
        self.assertIn("build_lab_snapshot", data["how"])


class InspectTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.dict("os.environ", {"AI_XAI_LAB_ENABLED": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.c = client()

    def test_빠듯한_입력은_high이고_네_요인이_모두_불리하다(self) -> None:
        data = self.c.post(f"{BASE}/inspect", json=INPUT).json()

        self.assertTrue(data["enabled"])
        self.assertEqual(data["risk_bucket"], "high")
        self.assertAlmostEqual(sum(data["probabilities"].values()), 1.0, places=5)
        for group in data["groups"]:
            self.assertLess(group["favorability"], 0)

    def test_여유_있는_입력은_low이고_네_요인이_모두_유리하다(self) -> None:
        data = self.c.post(f"{BASE}/inspect", json=HEALTHY).json()

        self.assertEqual(data["risk_bucket"], "low")
        for group in data["groups"]:
            self.assertGreater(group["favorability"], 0)

    def test_열별_기여도의_합과_기준값이_high_margin이다(self) -> None:
        data = self.c.post(f"{BASE}/inspect", json=INPUT).json()

        total = sum(f["risk_contribution"] for f in data["features"])
        self.assertAlmostEqual(data["base_margin"] + total, data["high_margin"], places=6)
        self.assertEqual(len(data["features"]), 10)

    def test_열은_기여도_절대값_순으로_정렬된다(self) -> None:
        data = self.c.post(f"{BASE}/inspect", json=INPUT).json()

        magnitudes = [abs(f["risk_contribution"]) for f in data["features"]]
        self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))

    def test_파생_열_값이_모델_안에서_계산된_값이다(self) -> None:
        data = self.c.post(f"{BASE}/inspect", json=INPUT).json()

        values = {f["name"]: f["value"] for f in data["features"]}
        self.assertAlmostEqual(values["product_price_vs_monthly_spending"], 2_500_000 / 1_300_000)
        self.assertAlmostEqual(values["projected_balance_after_purchase"], 150_000 - 2_500_000)

    def test_잘못된_입력은_422다(self) -> None:
        for bad in ({**INPUT, "price": 0}, {**INPUT, "current_balance": -1}, {**INPUT, "days_until_card_due": 40},
                    {k: v for k, v in INPUT.items() if k != "monthly_spending_30d"}, {**INPUT, "price": "비쌈"}):
            with self.subTest(bad=bad):
                self.assertEqual(self.c.post(f"{BASE}/inspect", json=bad).status_code, 422)

    def test_서비스는_비유한_값을_거부한다(self) -> None:
        with self.assertRaises(ValueError):
            service.inspect_finance(price=float("nan"), profile={k: v for k, v in INPUT.items() if k != "price"})


class SimulateTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.dict("os.environ", {"AI_XAI_LAB_ENABLED": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.c = client()

    def test_운영_판단_경로를_그대로_돌린다(self) -> None:
        data = self.c.post(f"{BASE}/simulate", json=INPUT).json()

        self.assertEqual(data["decision"], "NOT_RECOMMENDED")
        self.assertEqual(data["runtimeEngines"]["shap"], "shap_tree")
        self.assertTrue(data["counterfactuals"])
        self.assertTrue(all(c["validated"] for c in data["counterfactuals"]))

    def test_입력한_월_지출이_판단에_반영된다(self) -> None:
        """월 지출은 거래에서 계산된다. 입력값이 거래 한 건이 되어 그대로 쓰여야 한다."""
        low = self.c.post(f"{BASE}/simulate", json={**HEALTHY, "price": 600_000, "monthly_spending_30d": 3_000_000}).json()
        high = self.c.post(f"{BASE}/simulate", json={**HEALTHY, "price": 600_000, "monthly_spending_30d": 300_000}).json()

        def ratio_label(r):
            return next((f["label"] for f in r["topFactors"] if f["code"] == "PRICE_TOO_LARGE_VS_MONTHLY_SPENDING"), None)

        self.assertNotEqual(ratio_label(low), ratio_label(high))

    def test_감사_로그에_남기지_않는다(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "audit.jsonl"
            with patch("domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(log)):
                self.assertEqual(self.c.post(f"{BASE}/simulate", json=INPUT).status_code, 200)

            self.assertFalse(log.exists() and log.read_text(encoding="utf-8").strip())

    def test_운영_경로는_여전히_감사_로그에_남긴다(self) -> None:
        from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest
        from domain.xai_purchase.service import evaluate_pr_purchase_xai

        request = PurchaseXaiEvaluationRequest.model_validate({
            "requestId": "r", "schemaVersion": "v1", "contextVersion": "v1",
            "purchase": {"postId": 1, "title": "t", "itemName": "i", "content": "c", "category": "IT",
                         "purchaseUrl": None, "priceAmount": {"value": 50000, "source": "t", "snapshotId": "s"}},
            "financeProfile": {k: {"value": v, "source": "t", "snapshotId": "s"} for k, v in {
                "currentBalance": 1_000_000, "emergencyFundBalance": 500_000,
                "expectedCardPaymentAmount": 100_000, "daysUntilCardDue": 10}.items()},
            "recentTransactions": [],
        })
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "audit.jsonl"
            with patch("domain.xai_purchase.service._AUDIT_STORE", JsonlXaiAuditLogStore(log)):
                evaluate_pr_purchase_xai(request)

            self.assertTrue(log.read_text(encoding="utf-8").strip())


class BudgetLabTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.dict("os.environ", {"AI_XAI_LAB_ENABLED": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.c = client()
        self.base = {**HEALTHY, "monthly_spending_30d": 400_000, **BUDGET}

    def simulate(self, **override):
        res = self.c.post(f"{BASE}/simulate", json={**self.base, **override})
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()

    def test_모델_지도에_예산_노드가_있고_규칙_엔진으로_이어진다(self) -> None:
        data = self.c.get(f"{BASE}/overview").json()

        nodes = {n["id"]: n for n in data["nodes"]}
        self.assertEqual(nodes["budget_rule"]["status"], "ok")
        facts = dict(nodes["budget_rule"]["facts"])
        self.assertIn("0.5", facts["한도"])
        self.assertIn("90%", facts["여유 있음"])
        self.assertIn("기본값으로 추측하지 않음", nodes["budget_rule"]["caveat"])
        self.assertIn(["contract", "budget_rule"], data["edges"])
        self.assertIn(["budget_rule", "decision"], data["edges"])

    def test_소득과_고정지출을_넣으면_예산_평가가_같이_나온다(self) -> None:
        data = self.simulate(price=300_000)

        budget = data["lab"]["budget"]
        self.assertEqual(budget["status"], "over")
        self.assertEqual((budget["limit"], budget["used_before"], budget["used_after"]), (1_500_000, 1_300_000, 1_600_000))
        self.assertEqual(data["decision"], "NOT_RECOMMENDED")

    def test_화면용_예산_값은_운영_응답의_지표와_일치한다(self) -> None:
        for price in (50_000, 100_000, 300_000):
            with self.subTest(price=price):
                data = self.simulate(price=price)
                budget = data["lab"]["budget"]
                metrics = {m["code"]: m["value"] for m in data["financialEvaluation"]["keyMetrics"]}

                self.assertEqual(metrics["budget_zone_limit"], f"{int(budget['limit']):,}원")
                self.assertEqual(metrics["budget_zone_used_after"],
                                 f"{int(budget['used_after']):,}원 ({budget['used_after'] / budget['limit']:.0%})")

    def test_소득을_비우면_판단_안_함이고_운영과_같은_경고가_나온다(self) -> None:
        data = self.simulate(monthly_income=None)

        self.assertEqual(data["lab"]["budget"]["status"], "unavailable")
        self.assertEqual(data["lab"]["budget"]["reason"], "income_not_provided_by_upstream")
        self.assertIn("BUDGET_RULE_UNAVAILABLE:income_not_provided_by_upstream", data["warnings"])

    def test_고정지출만_비워도_판단_안_함이고_사유가_운영과_같다(self) -> None:
        data = self.simulate(fixed_expense=None)

        self.assertEqual(data["lab"]["budget"]["reason"], "fixed_expense_not_provided_by_upstream")
        self.assertIn("BUDGET_RULE_UNAVAILABLE:fixed_expense_not_provided_by_upstream", data["warnings"])

    def test_예산_판단이_결정에_반영된다(self) -> None:
        """같은 재무 상태에서 가격만 바꿔 한도를 넘기면 결정이 바뀐다."""
        within = self.simulate(price=50_000)
        over = self.simulate(price=300_000)

        self.assertNotEqual(within["decision"], over["decision"])
        self.assertEqual(over["decision"], "NOT_RECOMMENDED")

    def test_inspect_도_예산_입력을_받아도_재무_모델_입력은_바뀌지_않는다(self) -> None:
        plain = self.c.post(f"{BASE}/inspect", json={k: v for k, v in self.base.items() if k not in BUDGET})
        with_budget = self.c.post(f"{BASE}/inspect", json=self.base)

        self.assertEqual(with_budget.status_code, 200, with_budget.text)
        self.assertEqual(plain.json()["probabilities"], with_budget.json()["probabilities"])

    def test_잘못된_예산_입력은_422(self) -> None:
        for bad in ({"monthly_income": 0}, {"monthly_income": -1}, {"fixed_expense": -1}, {"monthly_income": "많음"}):
            with self.subTest(bad=bad):
                self.assertEqual(self.c.post(f"{BASE}/simulate", json={**self.base, **bad}).status_code, 422)


class PageTest(unittest.TestCase):
    html = PAGE.read_text(encoding="utf-8")

    def test_외부_주소를_부르지_않는다(self) -> None:
        """온프레미스에서 그대로 열려야 한다. CDN 스크립트/스타일/폰트가 없어야 한다."""
        self.assertIsNone(re.search(r'(?:src|href)\s*=\s*["\']https?://', self.html))
        self.assertNotIn("@import", self.html)
        self.assertNotIn("cdn.", self.html)

    def test_다섯_섹션이_있다(self) -> None:
        for section in ("map", "validation", "distributions", "performance", "simulator"):
            self.assertIn(f'id="{section}"', self.html)

    def test_페이지가_부르는_API는_모두_라우터에_있다(self) -> None:
        called = set(re.findall(r"\$\{API\}/(\w+)", self.html))
        # include 된 라우터는 app.routes 에 경로 없는 객체로 보이므로 OpenAPI 스키마로 확인한다.
        routes = {path.rsplit("/", 1)[-1] for path in app.openapi()["paths"] if path.startswith(BASE)}

        self.assertTrue(called)
        self.assertTrue(called <= routes, f"{called - routes}")

    def test_예산_입력과_게이지를_그린다(self) -> None:
        self.assertIn('["monthly_income"', self.html)
        self.assertIn('["fixed_expense"', self.html)
        self.assertIn("function renderBudget", self.html)
        self.assertIn("sim.lab", self.html)

    def test_사용자_입력을_이스케이프해_그리는_도우미가_있다(self) -> None:
        self.assertIn("const esc =", self.html)

    def test_성능_점수를_정확도로_오해하지_않게_경고한다(self) -> None:
        self.assertIn("정확도가 아닙니다", self.html)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
