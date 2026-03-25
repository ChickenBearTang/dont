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
from domain.xai_purchase.service import evaluate_pr_purchase_xai


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
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(None, "MISSING_PURCHASE_URL"),
        ):
            response = evaluate_pr_purchase_xai(_request())

        self.assertEqual(response.request_id, "req-456")
        self.assertEqual(response.purchase_request_id, 91)
        self.assertIn(
            response.decision, {"BUY_NOW", "WAIT", "REVIEW", "NOT_RECOMMENDED"}
        )
        self.assertTrue(len(response.top_factors) >= 1)
        self.assertTrue(len(response.supporting_evidence) >= 1)
        self.assertIn("runtime_engines", response.model_dump())

    def test_request_price_takes_priority_over_noisy_crawled_value(self) -> None:
        with patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=("배송비 1,796원 / 특가 2,500,000원 아님", None),
        ):
            response = evaluate_pr_purchase_xai(_request())

        price_metrics = {
            metric.code: metric.value
            for metric in response.price_evaluation.key_metrics
        }
        self.assertEqual(price_metrics.get("current_effective_price"), "189,000원")
        self.assertEqual(price_metrics.get("requested_price_amount"), "189,000원")
        self.assertEqual(price_metrics.get("crawled_price_candidate"), "2,500,000원")
        self.assertIn("CRAWLED_PRICE_DIVERGES_FROM_REQUEST", response.warnings)

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


if __name__ == "__main__":
    unittest.main()
