from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from domain.xai_purchase.schemas import PurchaseXaiEvaluationRequest
from domain.xai_purchase.service import evaluate_pr_purchase_xai


class XaiPurchasePriceOnlyFallbackTest(unittest.TestCase):
    def test_finance_all_zero_uses_price_only_fallback(self) -> None:
        request = PurchaseXaiEvaluationRequest.model_validate(
            {
                "requestId": "req-price-only-fallback",
                "schemaVersion": "v1",
                "contextVersion": "v1",
                "purchase": {
                    "postId": 501,
                    "title": "fallback-check",
                    "itemName": "keyboard",
                    "content": "fallback-check",
                    "category": "IT",
                    "purchaseUrl": "https://example.com/item-501",
                    "priceAmount": {
                        "value": 70000,
                        "source": "spring.pr_post",
                        "snapshotId": "pr-501",
                    },
                },
                "financeProfile": {
                    "currentBalance": {
                        "value": 0,
                        "source": "spring.finance_profile",
                        "snapshotId": "fin-501",
                    },
                    "emergencyFundBalance": {
                        "value": 0,
                        "source": "spring.finance_profile",
                        "snapshotId": "fin-501",
                    },
                    "saveboxBalance": {
                        "value": 0,
                        "source": "spring.savebox",
                        "snapshotId": "savebox-501",
                    },
                    "expectedCardPaymentAmount": {
                        "value": 0,
                        "source": "spring.finance_profile",
                        "snapshotId": "fin-501",
                    },
                    "daysUntilCardDue": {
                        "value": 7,
                        "source": "spring.finance_profile",
                        "snapshotId": "fin-501",
                    },
                },
                "recentTransactions": [],
            }
        )

        with patch(
            "domain.xai_purchase.service._read_window_stats",
            return_value=(
                {
                    "30d": {
                        "count": 12,
                        "avg_price": 100000.0,
                        "min_price": 90000.0,
                        "max_price": 110000.0,
                    }
                },
                [],
            ),
        ), patch(
            "domain.xai_purchase.service._fetch_page_text",
            return_value=(None, "MISSING_PURCHASE_URL"),
        ):
            response = evaluate_pr_purchase_xai(request)

        self.assertEqual(response.price_evaluation.status, "favorable")
        self.assertEqual(response.financial_evaluation.status, "degraded")
        self.assertEqual(response.decision, "BUY_NOW")
        self.assertIn("FINANCE_PROFILE_EMPTY_FALLBACK", response.warnings)
        self.assertTrue(
            response.summary.startswith("구매 권장. 핵심 근거:"),
            msg=response.summary,
        )
        self.assertTrue(
            any(factor.code == "PRICE_ONLY_FALLBACK" for factor in response.top_factors)
        )
        self.assertEqual(response.counterfactuals, [])


if __name__ == "__main__":
    unittest.main()
