from __future__ import annotations

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
from domain.xai_purchase.service import (
    _counterfactual_target_decision,
    evaluate_pr_purchase_xai,
)


def _request() -> PurchaseXaiEvaluationRequest:
    return PurchaseXaiEvaluationRequest.model_validate(
        {
            "requestId": "req-456",
            "schemaVersion": "v1",
            "contextVersion": "v1",
            "purchase": {
                "postId": 91,
                "title": "키보드 구매 요청",
                "itemName": "기계식 키보드",
                "content": "개발 생산성 향상을 위해 필요합니다.",
                "category": "IT",
                "purchaseUrl": "https://example.com/keyboard",
                "priceAmount": {
                    "value": 189000,
                    "source": "spring.pr_post",
                    "snapshotId": "pr-91",
                },
            },
            "financeProfile": {
                "currentBalance": {
                    "value": 1200000,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
                "emergencyFundBalance": {
                    "value": 700000,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
                "expectedCardPaymentAmount": {
                    "value": 150000,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
                "daysUntilCardDue": {
                    "value": 12,
                    "source": "spring.finance_profile",
                    "snapshotId": "fin-91",
                },
            },
            "recentTransactions": [],
        }
    )


class XaiPurchaseServiceTest(unittest.TestCase):
    def test_evaluate_pr_purchase_xai_returns_normalized_response(self) -> None:
        response = evaluate_pr_purchase_xai(_request())

        self.assertEqual(response.request_id, "req-456")
        self.assertEqual(response.purchase_request_id, 91)
        self.assertIn(
            response.decision, {"BUY_NOW", "WAIT", "REVIEW", "NOT_RECOMMENDED"}
        )
        self.assertTrue(len(response.top_factors) >= 1)
        self.assertTrue(len(response.supporting_evidence) >= 1)
        self.assertIn("runtime_engines", response.model_dump())

    def test_request_price_is_the_effective_price(self) -> None:
        response = evaluate_pr_purchase_xai(_request())

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertEqual(price_metrics.get("current_effective_price"), "189,000원")

    def test_summary_and_top_factors_are_localized_in_korean(self) -> None:
        response = evaluate_pr_purchase_xai(_request())

        self.assertRegex(response.summary, r"[가-힣]")
        self.assertGreaterEqual(len(response.top_factors), 1)
        for factor in response.top_factors:
            self.assertRegex(factor.label, r"[가-힣]")

    def test_missing_request_price_shows_a_dash(self) -> None:
        request = _request()
        request.purchase.price_amount.value = None

        response = evaluate_pr_purchase_xai(request)

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertEqual(price_metrics.get("current_effective_price"), "-")

    def test_financial_status_uses_savebox_and_fixed_cashflow_fields(self) -> None:
        payload = _request().model_dump(by_alias=True)
        payload["financeProfile"]["currentBalance"]["value"] = 12_912_010
        payload["financeProfile"]["daysUntilCardDue"]["value"] = 10
        payload["financeProfile"]["saveboxBalance"] = {
            "value": 0,
            "source": "spring.finance_profile",
            "snapshotId": "fin-91",
        }
        payload["financeProfile"]["availableFixedExpense"] = {
            "value": 400000,
            "source": "spring.finance_profile",
            "snapshotId": "fin-91",
        }
        payload["financeProfile"]["availableFixedIncome"] = {
            "value": 300000,
            "source": "spring.finance_profile",
            "snapshotId": "fin-91",
        }
        request = PurchaseXaiEvaluationRequest.model_validate(payload)

        with patch(
            "domain.xai_purchase.service.predict_finance_signal",
            return_value=(
                {},
                {"enabled": False, "backend": "disabled", "reason": "finance_model_disabled"},
            ),
        ):
            response = evaluate_pr_purchase_xai(request)

        self.assertEqual(response.financial_evaluation.status, "critical")
        financial_metrics = {
            metric.code: metric.value
            for metric in response.financial_evaluation.key_metrics
        }
        self.assertEqual(financial_metrics.get("savebox_balance"), "0원")
        self.assertEqual(financial_metrics.get("available_fixed_expense"), "400,000원")
        self.assertEqual(financial_metrics.get("available_fixed_income"), "300,000원")
        self.assertEqual(financial_metrics.get("days_until_card_due"), "10일")

    def test_financial_metrics_hide_defaulted_fixed_income_and_expense(self) -> None:
        """앞단이 안 보낸 고정 수입/지출은 기본값(100만 원/0원)으로 채워지는데, 그 값을 사실처럼 보여주지 않는다."""
        request = _request()

        with patch(
            "domain.xai_purchase.service.predict_finance_signal",
            return_value=(
                {},
                {"enabled": False, "backend": "disabled", "reason": "finance_model_disabled"},
            ),
        ):
            response = evaluate_pr_purchase_xai(request)

        financial_metrics = {
            metric.code: metric.value
            for metric in response.financial_evaluation.key_metrics
        }
        self.assertNotIn("available_fixed_expense", financial_metrics)
        self.assertNotIn("available_fixed_income", financial_metrics)
        self.assertEqual(financial_metrics.get("expected_card_payment_amount"), "150,000원")
        # 숨기는 대신 기본값이 쓰였다는 사실은 경고로 남는다.
        self.assertIn("FINANCE_FIELD_DEFAULTED:available_fixed_income", response.warnings)
        self.assertIn("FINANCE_FIELD_DEFAULTED:available_fixed_expense", response.warnings)

    def test_jsonl_audit_store_persists_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = JsonlXaiAuditLogStore(Path(tmp_dir) / "audit.jsonl")
            store.save(
                request_id="req-1",
                purchase_request_id=10,
                warnings=["NO_PRICE_HISTORY"],
                runtime_engines={"decision": "rule_engine_v1"},
                audit_logs=[
                    {"final_decision": "REVIEW", "item_id": "https://example.com"}
                ],
            )

            saved = (Path(tmp_dir) / "audit.jsonl").read_text(encoding="utf-8")
            self.assertIn("req-1", saved)
            self.assertIn("NO_PRICE_HISTORY", saved)
            self.assertIn("REVIEW", saved)

    def test_counterfactual_target_decision_respects_wait_action(self) -> None:
        target = _counterfactual_target_decision(
            current_decision="REVIEW",
            counterfactual={
                "action": "wait_for_better_price",
                "suggested_change": 0,
            },
        )
        self.assertEqual(target, "WAIT")

    def test_counterfactual_target_decision_keeps_review_when_no_change(self) -> None:
        target = _counterfactual_target_decision(
            current_decision="REVIEW",
            counterfactual={
                "action": "increase",
                "suggested_change": 0,
            },
        )
        self.assertEqual(target, "REVIEW")


if __name__ == "__main__":
    unittest.main()
